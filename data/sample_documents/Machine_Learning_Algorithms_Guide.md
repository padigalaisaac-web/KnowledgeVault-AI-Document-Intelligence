# Comprehensive Machine Learning Algorithms & Evaluation Metrics Guide

## 1. Overview of Supervised Learning Algorithms

Supervised learning algorithms infer a function from labeled training data consisting of input features and desired target outputs.

### 1.1 Random Forest Classifier & Regressor
Random Forest is an ensemble learning method that constructs a multitude of decision trees at training time. For classification tasks, the output is the class selected by the majority of trees; for regression tasks, the mean or average prediction of the individual trees is returned.
- **Ensemble Technique**: Bootstrap aggregating (bagging). Each tree is trained on a random bootstrap sample with replacement from the training set.
- **Feature Subsampling**: At each candidate split, a random subset of features (typically $\sqrt{p}$ for classification and $p/3$ for regression, where $p$ is the total number of features) is considered to decorrelate individual trees.
- **Splitting Criteria**: Gini Impurity $I_G(p) = 1 - \sum_{i=1}^J p_i^2$ or Information Gain based on Shannon Entropy $H(X) = -\sum p_i \log_2(p_i)$.
- **Out-of-Bag (OOB) Error**: Since bootstrap sampling leaves approximately $36.8\%$ of instances out of each tree's training set, OOB samples serve as an internal cross-validation mechanism without requiring a separate validation set.

### 1.2 Gradient Boosted Decision Trees (GBDT, XGBoost, LightGBM)
Gradient boosting builds trees sequentially, with each subsequent tree trained to predict the pseudo-residuals (negative gradient of the loss function) of the existing ensemble.
- **Objective Function**: Combines a differentiable loss function $\mathcal{L}(\hat{y}, y)$ with a regularization term $\Omega(f) = \gamma T + \frac{1}{2}\lambda \sum w_j^2$ penalizing tree complexity and leaf weights.
- **Shrinkage Parameter**: A learning rate $\eta \in (0, 1]$ scales the contribution of each newly added tree, preventing overfitting.
- **Handling Sparsity**: Modern libraries like XGBoost implement a default split direction for missing values and histogram-based binning (LightGBM) to accelerate computation.

### 1.3 Support Vector Machines (SVM)
Support Vector Machines identify the optimal hyperplane that maximizes the geometric margin between two distinct classes in feature space.
- **Optimization Formulation**: Minimizes $\frac{1}{2}\|w\|^2 + C \sum \xi_i$ subject to $y_i(w^T x_i + b) \ge 1 - \xi_i$, where $\xi_i \ge 0$ are slack variables and $C$ is the regularization parameter governing margin violation penalty.
- **Kernel Trick**: Projects non-linearly separable data into higher-dimensional Hilbert spaces using Mercer kernel functions such as the Radial Basis Function (RBF) $K(x, x') = \exp(-\gamma \|x - x'\|^2)$ and polynomial kernels $K(x, x') = (x^T x' + c)^d$.

---

## 2. Deep Learning & The Transformer Architecture

Transformers rely entirely on attention mechanisms without recurrence or convolutions, enabling massive parallelism across sequence tokens.

### 2.1 Self-Attention Mechanism
The core building block is Scaled Dot-Product Attention:
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$
Where:
- $Q \in \mathbb{R}^{n \times d_k}$ represents the Query matrix.
- $K \in \mathbb{R}^{m \times d_k}$ represents the Key matrix.
- $V \in \mathbb{R}^{m \times d_v}$ represents the Value matrix.
- $\sqrt{d_k}$ is the scaling factor counteracting vanishing softmax gradients for large projection dimensions.

### 2.2 Multi-Head Attention
Instead of performing a single attention function, Multi-Head Attention linearly projects queries, keys, and values $h$ times with learned parameter matrices $W_i^Q, W_i^K, W_i^V$:
$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \dots, \text{head}_h)W^O$$
$$\text{where } \text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

---

## 3. Evaluation Metrics for Classification, Ranking, and Generation

Selecting the correct evaluation metric depends strictly on data distribution, class balance, and the downstream operational cost of errors.

### 3.1 Classification Metrics
- **Precision**: $\text{Precision} = \frac{\text{True Positives (TP)}}{\text{True Positives (TP)} + \text{False Positives (FP)}}$. Measures the fidelity of positive predictions. Critical in spam detection and automated medical diagnosis where false alarms carry substantial cost.
- **Recall (Sensitivity)**: $\text{Recall} = \frac{\text{True Positives (TP)}}{\text{True Positives (TP)} + \text{False Negatives (FN)}}$. Measures the coverage of positive cases. Vital in cancer screening and fraud detection where missing a true positive is catastrophic.
- **F1-Score**: The harmonic mean of precision and recall:
  $$F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}} = \frac{2 \cdot \text{TP}}{2 \cdot \text{TP} + \text{FP} + \text{FN}}$$
- **Macro-F1 vs Micro-F1 vs Weighted-F1**:
  - Macro-F1 calculates unweighted metrics for each class independently, treating all classes with equal importance regardless of frequency.
  - Micro-F1 aggregates global TP, FP, and FN across all classes, biasing the score toward majority classes.
  - Weighted-F1 averages class F1-scores weighted by their support (true instance count).
- **ROC-AUC**: The Area Under the Receiver Operating Characteristic curve measures discrimination ability across all classification thresholds, plotting True Positive Rate vs False Positive Rate.
- **PR-AUC (Average Precision)**: Preferred over ROC-AUC in severe class imbalance settings because it does not incorporate True Negatives.

### 3.2 Ranking & Retrieval Metrics
- **Mean Reciprocal Rank (MRR)**: Evaluates systems that return an ordered list of items:
  $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
  where $\text{rank}_i$ is the position of the first relevant item for query $i$.
- **Recall@K**: Proportion of total relevant items retrieved within the top $K$ positions.
- **Normalized Discounted Cumulative Gain (NDCG@K)**: Accounts for graded relevance and penalizes relevant items ranked lower down the list using logarithmic discount factors $\log_2(i + 1)$.

### 3.3 Text Generation Metrics
- **BLEU**: Measures n-gram precision between generated text and reference text with a brevity penalty.
- **ROUGE (ROUGE-1, ROUGE-2, ROUGE-L)**: Measures n-gram recall and longest common subsequence for summarization tasks.
- **Faithfulness (RAG Triad)**: Measures whether claims in the generated answer can be strictly deduced from retrieved context passages.
