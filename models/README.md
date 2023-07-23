# Models

**This folder contains the experiments performed during the development of the trading bot.**

---

There are two seperate directories for the two different models within which each subdirectory represents a different experiment and contains the following files:

- `params.json`: the list of hyperparameters used in the experiment, in JSON format
- `train.log`: the training log, including everything printed to the console during training
- `train_summaries`: train summaries for TensorBoard (TensorFlow only)
- `eval_summaries`: eval summaries for TensorBoard (TensorFlow only)
- `last_weights`: weights saved from the 5 last epochs
- `best_weights`: best weights based on dev accuracy
- `README.md`: a brief summary of the experiment, its purpose, and any notable results or observations
- `evaluation.ipynb`: a notebook that can be used to evaluate the performance of the trained model

---

- `comparison.ipynb`: a notebook used to compare the performance of different models