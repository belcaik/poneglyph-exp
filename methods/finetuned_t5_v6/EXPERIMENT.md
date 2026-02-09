# T5 v6 Experiment: MATCHA Exclusion

## Hypothesis
MATCHA's low annotation coverage (66.2%) and bracket collisions are introducing
noise that hurts model generalization. Excluding it should improve accuracy
despite reducing training data.

## Dataset composition

### v5 (baseline)
- NHK: ~2,284 sentences
- MATCHA: ~13,713 sentences (EXCLUDED in v6)
- Kahoku: ~1,198 sentences
- Hirogaru: ~506 sentences
- UD GSD: ~8,036 sentences
- UD PUD: ~996 sentences
- Total: ~26,733 sentences

### v6 (this experiment)
- NHK: ~2,284 sentences
- Kahoku: ~1,198 sentences
- Hirogaru: ~506 sentences
- UD GSD: ~8,036 sentences
- UD PUD: ~996 sentences
- Total: ~13,020 sentences (estimated)

## Evaluation
Compare v6 vs v5 on the v5 test set (excluding MATCHA test samples for fair comparison).

## Results

(To be filled after training and evaluation)
