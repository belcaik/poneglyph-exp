"""SpanReader: Unified span query model for furigana annotation.

Uses learned span queries with cross-attention (DETR-inspired) to jointly
predict span positions, types, and readings in a single forward pass.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.optimize import linear_sum_assignment


class CharPooling(nn.Module):
    """Pool subword token representations to character-level with intra-token position encoding.

    When DeBERTa tokenizes '少ない' as ['少', 'ない'], chars な and い both map
    to the same token. Without positional disambiguation, the end position head
    cannot distinguish them. The intra-token position embedding solves this by
    giving each character a unique representation based on its position within
    the token (0th char, 1st char, etc.).
    """

    def __init__(self, hidden_size=768, max_chars_per_token=8):
        super().__init__()
        self.intra_token_pos = nn.Embedding(max_chars_per_token, hidden_size)
        self.max_intra = max_chars_per_token

    def forward(self, token_hidden, char_to_token, char_mask, intra_positions=None):
        """
        Args:
            token_hidden: (batch, num_tokens, hidden) — encoder output
            char_to_token: (batch, num_chars) — token index for each char
            char_mask: (batch, num_chars) — 1 for real chars, 0 for padding
            intra_positions: (batch, num_chars) — position within token (precomputed)
        Returns:
            char_hidden: (batch, num_chars, hidden)
        """
        batch_size, num_chars = char_to_token.shape
        indices = char_to_token.clamp(0, token_hidden.size(1) - 1)

        # Gather token representation for each character
        char_hidden = torch.gather(
            token_hidden, 1,
            indices.unsqueeze(-1).expand(-1, -1, token_hidden.size(-1))
        )

        # Compute intra-token positions if not precomputed
        if intra_positions is None:
            intra_positions = self._compute_intra_positions(char_to_token)

        # Add within-token positional encoding — this is the key fix!
        # Now な (pos=0 within 'ない') and い (pos=1) get different representations
        pos_enc = self.intra_token_pos(intra_positions.clamp(0, self.max_intra - 1))
        char_hidden = char_hidden + pos_enc

        char_hidden = char_hidden * char_mask.unsqueeze(-1)
        return char_hidden

    @staticmethod
    def _compute_intra_positions(char_to_token):
        """Compute within-token position for each character.

        Example: char_to_token = [1, 1, 2, 3, 3, 3, 4]
        Result:  intra_pos    = [0, 1, 0, 0, 1, 2, 0]
        """
        batch_size, num_chars = char_to_token.shape
        device = char_to_token.device
        intra_pos = torch.zeros_like(char_to_token)

        for b in range(batch_size):
            tokens = char_to_token[b]
            # Detect where the token index changes
            changes = torch.ones(num_chars, dtype=torch.bool, device=device)
            changes[1:] = tokens[1:] != tokens[:-1]
            # Build cumulative count within each group
            count = 0
            for i in range(num_chars):
                if changes[i]:
                    count = 0
                intra_pos[b, i] = count
                count += 1

        return intra_pos.clamp(max=7)


class PositionHead(nn.Module):
    """Pointer attention from queries to character positions."""

    def __init__(self, d_model, d_proj=256):
        super().__init__()
        self.query_proj = nn.Linear(d_model, d_proj)
        self.char_proj = nn.Linear(d_model, d_proj)

    def forward(self, query_output, char_hidden):
        """
        Args:
            query_output: (batch, K, d_model)
            char_hidden: (batch, num_chars, d_model)
        Returns:
            logits: (batch, K, num_chars)
        """
        q = self.query_proj(query_output)
        c = self.char_proj(char_hidden)
        return torch.matmul(q, c.transpose(-1, -2))


class MicroDecoder(nn.Module):
    """Tiny autoregressive decoder for generating hiragana readings (OOV)."""

    def __init__(self, d_model=768, d_inner=256, n_layers=2, n_heads=4,
                 hiragana_vocab_size=90, max_reading_len=20):
        super().__init__()
        self.d_inner = d_inner
        self.max_reading_len = max_reading_len
        self.hiragana_vocab_size = hiragana_vocab_size

        self.embedding = nn.Embedding(hiragana_vocab_size, d_inner)
        self.pos_embedding = nn.Embedding(max_reading_len, d_inner)
        self.context_proj = nn.Linear(d_model, d_inner)

        decoder_layer = nn.TransformerDecoderLayer(
            d_model=d_inner, nhead=n_heads, dim_feedforward=512,
            dropout=0.1, activation='gelu', batch_first=True
        )
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers=n_layers)
        self.output_proj = nn.Linear(d_inner, hiragana_vocab_size)

    def forward(self, context, target_ids=None):
        """
        Args:
            context: (batch, context_len, d_model) — span hidden states
            target_ids: (batch, reading_len) — gold reading for teacher forcing
        Returns:
            logits: (batch, reading_len, vocab_size)
        """
        memory = self.context_proj(context)

        if target_ids is not None:
            # Teacher forcing
            seq_len = target_ids.size(1)
            tgt = self.embedding(target_ids)
            positions = torch.arange(seq_len, device=tgt.device).unsqueeze(0)
            tgt = tgt + self.pos_embedding(positions)
            # Causal mask
            causal_mask = nn.Transformer.generate_square_subsequent_mask(seq_len, device=tgt.device)
            decoded = self.decoder(tgt, memory, tgt_mask=causal_mask)
            return self.output_proj(decoded)
        else:
            # Autoregressive generation
            return self._generate(memory)

    def _generate(self, memory):
        """Greedy autoregressive generation."""
        batch_size = memory.size(0)
        device = memory.device
        # SOS token = 0 by convention
        current = torch.zeros(batch_size, 1, dtype=torch.long, device=device)
        outputs = []

        for step in range(self.max_reading_len):
            tgt = self.embedding(current)
            positions = torch.arange(current.size(1), device=device).unsqueeze(0)
            tgt = tgt + self.pos_embedding(positions)
            causal_mask = nn.Transformer.generate_square_subsequent_mask(
                current.size(1), device=device
            )
            decoded = self.decoder(tgt, memory, tgt_mask=causal_mask)
            logits = self.output_proj(decoded[:, -1:, :])
            next_token = logits.argmax(dim=-1)
            outputs.append(next_token)
            current = torch.cat([current, next_token], dim=1)
            # Stop if all batches generated EOS (token 1)
            if (next_token == 1).all():
                break

        return torch.cat(outputs, dim=1)


class SpanReaderModel(nn.Module):
    """Full SpanReader model."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.num_queries = config.get("num_queries", 30)
        self.num_types = config.get("num_types", 7)
        d_model = config.get("d_model", 768)
        reading_vocab_size = config.get("reading_vocab_size", 1)
        hiragana_vocab_size = config.get("hiragana_vocab_size", 90)

        # 1. Encoder
        from transformers import AutoModel
        encoder_name = config.get("encoder_name", "ku-nlp/deberta-v3-base-japanese")
        self.encoder = AutoModel.from_pretrained(encoder_name)

        # 2. Character pooling
        self.char_pool = CharPooling(hidden_size=d_model)

        # 3. Span queries
        self.span_queries = nn.Parameter(
            torch.randn(self.num_queries, d_model) * 0.02
        )

        # 4. Span query decoder
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=d_model, nhead=12, dim_feedforward=3072,
            dropout=0.1, activation='gelu', batch_first=True
        )
        self.span_decoder = nn.TransformerDecoder(decoder_layer, num_layers=2)

        # 5. Position heads
        self.start_head = PositionHead(d_model, d_proj=256)
        self.end_head = PositionHead(d_model, d_proj=256)

        # 6. Existence head
        self.exists_head = nn.Linear(d_model, 1)

        # 7. Type head
        self.type_head = nn.Linear(d_model, self.num_types)

        # 8. Reading classifier (for known surfaces)
        self.reading_classifier = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, reading_vocab_size),
        )

        # 9. Micro-decoder (for OOV)
        self.micro_decoder = MicroDecoder(
            d_model=d_model, hiragana_vocab_size=hiragana_vocab_size
        )

        # Loss weights
        self.lambda_exist = config.get("lambda_exist", 2.0)
        self.lambda_pos = config.get("lambda_pos", 5.0)
        self.lambda_type = config.get("lambda_type", 1.0)
        self.lambda_read_cls = config.get("lambda_read_cls", 3.0)
        self.lambda_read_gen = config.get("lambda_read_gen", 3.0)

    def encode_and_pool(self, input_ids, attention_mask, char_to_token, char_mask,
                        intra_positions=None):
        """Encode input and pool to character level."""
        encoder_output = self.encoder(
            input_ids=input_ids, attention_mask=attention_mask
        ).last_hidden_state  # (batch, num_tokens, d_model)

        char_hidden = self.char_pool(
            encoder_output, char_to_token, char_mask, intra_positions
        )
        return char_hidden, encoder_output

    def decode_queries(self, char_hidden):
        """Run span queries through the decoder."""
        batch_size = char_hidden.size(0)
        queries = self.span_queries.unsqueeze(0).expand(batch_size, -1, -1)
        query_output = self.span_decoder(queries, char_hidden)
        return query_output

    def forward(self, input_ids, attention_mask, char_to_token, char_mask,
                intra_positions=None,
                gold_spans=None, reading_targets=None, reading_target_masks=None,
                gen_targets=None, gen_context_indices=None):
        """
        Forward pass. Returns loss during training, predictions during inference.

        gold_spans: dict with keys 'start', 'end', 'type', 'exists', 'reading_idx'
                    each (batch, K) padded to K queries
        """
        char_hidden, encoder_output = self.encode_and_pool(
            input_ids, attention_mask, char_to_token, char_mask, intra_positions
        )
        query_output = self.decode_queries(char_hidden)

        # Predict
        start_logits = self.start_head(query_output, char_hidden)
        end_logits = self.end_head(query_output, char_hidden)
        exists_logits = self.exists_head(query_output).squeeze(-1)
        type_logits = self.type_head(query_output)
        reading_logits = self.reading_classifier(query_output)

        preds = {
            "start_logits": start_logits,
            "end_logits": end_logits,
            "exists_logits": exists_logits,
            "type_logits": type_logits,
            "reading_logits": reading_logits,
            "query_output": query_output,
        }

        if gold_spans is not None:
            loss = self.compute_loss(preds, gold_spans, char_hidden, char_mask,
                                     gen_targets, gen_context_indices)
            return loss, preds
        return preds

    def compute_loss(self, preds, gold, char_hidden, char_mask,
                     gen_targets=None, gen_context_indices=None):
        """Compute combined loss with Hungarian matching."""
        batch_size = preds["start_logits"].size(0)
        device = preds["start_logits"].device
        total_loss = torch.tensor(0.0, device=device)

        for b in range(batch_size):
            gold_exists = gold["exists"][b]  # (K,) — 1 for real spans
            num_gold = gold_exists.sum().int().item()

            if num_gold == 0:
                # No spans — only existence loss
                loss_exist = F.binary_cross_entropy_with_logits(
                    preds["exists_logits"][b],
                    torch.zeros(self.num_queries, device=device)
                )
                total_loss = total_loss + self.lambda_exist * loss_exist
                continue

            # Hungarian matching
            with torch.no_grad():
                cost = self._build_cost_matrix(preds, gold, b, num_gold)
                pred_idx, gold_idx = linear_sum_assignment(cost.cpu().numpy())
                pred_idx = torch.tensor(pred_idx, device=device, dtype=torch.long)
                gold_idx = torch.tensor(gold_idx, device=device, dtype=torch.long)

            # Existence loss (all queries)
            target_exists = torch.zeros(self.num_queries, device=device)
            target_exists[pred_idx] = 1.0
            loss_exist = F.binary_cross_entropy_with_logits(
                preds["exists_logits"][b], target_exists
            )

            # Position loss (matched only)
            num_chars = char_mask[b].sum().int().item()
            loss_start = F.cross_entropy(
                preds["start_logits"][b, pred_idx, :num_chars],
                gold["start"][b, gold_idx]
            )
            loss_end = F.cross_entropy(
                preds["end_logits"][b, pred_idx, :num_chars],
                gold["end"][b, gold_idx]
            )

            # Type loss (matched only)
            loss_type = F.cross_entropy(
                preds["type_logits"][b, pred_idx],
                gold["type"][b, gold_idx]
            )

            # Reading classification loss (matched queries with known readings)
            reading_mask = gold["reading_idx"][b, gold_idx] >= 0
            if reading_mask.any():
                loss_read_cls = F.cross_entropy(
                    preds["reading_logits"][b, pred_idx[reading_mask]],
                    gold["reading_idx"][b, gold_idx[reading_mask]]
                )
            else:
                loss_read_cls = torch.tensor(0.0, device=device)

            total_loss = total_loss + (
                self.lambda_exist * loss_exist
                + self.lambda_pos * (loss_start + loss_end)
                + self.lambda_type * loss_type
                + self.lambda_read_cls * loss_read_cls
            )

        return total_loss / batch_size

    def _build_cost_matrix(self, preds, gold, b, num_gold):
        """Build cost matrix for Hungarian matching."""
        device = preds["start_logits"].device
        K = self.num_queries

        # Start/end probabilities
        start_probs = preds["start_logits"][b].softmax(-1)  # (K, L)
        end_probs = preds["end_logits"][b].softmax(-1)  # (K, L)

        cost = torch.zeros(K, num_gold, device=device)

        for j in range(num_gold):
            gs = gold["start"][b, j].item()
            ge = gold["end"][b, j].item()
            gt = gold["type"][b, j].item()

            # Position cost: negative log-prob of gold position
            cost[:, j] += 5.0 * (-start_probs[:, gs].log().clamp(min=-10))
            cost[:, j] += 5.0 * (-end_probs[:, ge].log().clamp(min=-10))

            # Existence cost: cost of NOT predicting existence
            exist_prob = torch.sigmoid(preds["exists_logits"][b])
            cost[:, j] += 2.0 * (-exist_prob.log().clamp(min=-10))

            # Type cost
            type_probs = preds["type_logits"][b].softmax(-1)
            cost[:, j] += 1.0 * (-type_probs[:, gt].log().clamp(min=-10))

        return cost

    @torch.no_grad()
    def predict(self, input_ids, attention_mask, char_to_token, char_mask,
                intra_positions=None,
                reading_vocab=None, global_readings=None, threshold=0.5):
        """Run inference and extract spans."""
        self.eval()
        preds = self.forward(input_ids, attention_mask, char_to_token, char_mask,
                             intra_positions=intra_positions)

        batch_size = input_ids.size(0)
        results = []

        for b in range(batch_size):
            num_chars = char_mask[b].sum().int().item()
            exists_prob = torch.sigmoid(preds["exists_logits"][b])
            active = exists_prob > threshold

            spans = []
            for q in range(self.num_queries):
                if not active[q]:
                    continue

                start = preds["start_logits"][b, q, :num_chars].argmax().item()
                end = preds["end_logits"][b, q, :num_chars].argmax().item()
                if end < start:
                    end = start

                span_type = preds["type_logits"][b, q].argmax().item()
                reading_idx = preds["reading_logits"][b, q].argmax().item()

                reading = ""
                if global_readings and 0 <= reading_idx < len(global_readings):
                    reading = global_readings[reading_idx]

                spans.append({
                    "start": start,
                    "end": end + 1,  # exclusive
                    "type_idx": span_type,
                    "reading": reading,
                    "confidence": exists_prob[q].item(),
                })

            # Sort by start position, deduplicate overlapping spans
            spans.sort(key=lambda s: (s["start"], -s["confidence"]))
            deduped = []
            used_positions = set()
            for s in spans:
                positions = set(range(s["start"], s["end"]))
                if not positions & used_positions:
                    deduped.append(s)
                    used_positions |= positions

            results.append(deduped)

        return results
