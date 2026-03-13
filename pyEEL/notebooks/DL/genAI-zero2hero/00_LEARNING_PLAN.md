# Deep Learning Mastery in 3 Weeks
## A Coach-Style Learning Plan for Builders

---

## YOUR PROFILE
- **Level:** Beginner (with CS & programming background)
- **Goal:** Build and deploy a full-stack app using deep learning
- **Time:** 4 hours/week × 3 weeks = 12 hours total
- **Style:** Hands-on / Mixed

---

## 1. ROADMAP OVERVIEW

```
WEEK 1                    WEEK 2                      WEEK 3
[Foundations]         →   [Going Deep]           →    [Generate & Deploy]
                          
MILESTONE 1               MILESTONE 2                 MILESTONE 3
Build a neural net         Train a deep network        Build & deploy a
from SCRATCH in            in PyTorch that              generative AI app
pure Python. Explain       outperforms your             (image or text)
every line.                Week 1 model.                end-to-end.
                          
YOU CAN:                   YOU CAN:                    YOU CAN:
✓ Code forward pass       ✓ Choose architectures      ✓ Build a VAE/simple
✓ Code backprop           ✓ Debug vanishing grads        generative model
✓ Explain ReLU vs         ✓ Use BatchNorm,            ✓ Deploy with Flask
  sigmoid tradeoffs         He init, dropout             or Gradio
✓ Visualize decision      ✓ Explain overparams        ✓ Show a portfolio
  boundaries              ✓ Read loss landscapes         project
```

**FINAL MILESTONE (end of Week 3):**  
You have a deployed web app that uses a trained generative model, with a GitHub repo you can show anyone.

---

## 2. WEEK-BY-WEEK PLAN

### WEEK 1 — "Build a Brain from Scratch"
**Core concept:** Neural networks are just function approximators trained via gradient descent.

**Curriculum points covered:**
- ① Universal Approximation Theorem
- ② ReLU changed everything
- ⑤ Backpropagation is just the chain rule
- ④ Neural networks don't "understand" (they minimize loss)

**Resources (pick ONE per session):**
| Resource | Why This One |
|----------|-------------|
| **3Blue1Brown: "Neural Networks" (YouTube, Ch.1–4)** | Best visual intuition for backprop and gradient flow. 1 hour total. Nothing else builds geometric intuition this fast. |
| **Andrej Karpathy: "Neural Networks: Zero to Hero" Lecture 1 (YouTube)** | He live-codes a neural net from scratch. Exactly what you'll do in the notebooks. |
| **Michael Nielsen: "Neural Networks and Deep Learning" Ch.1–2 (neuralnetworksanddeeplearning.com)** | Best free text explanation of backprop. Read ONLY if you want the math derivation. |

**Build exercise:** Complete notebooks `W1_01` through `W1_03` (Pure Python series). You will:
1. Build a single neuron, then a full network, with no libraries
2. Implement backprop using only NumPy
3. Train on a real dataset and visualize decision boundaries

**"You know you've got it when..."**
- [ ] You can draw the computation graph for a 2-layer network on paper
- [ ] You can explain WHY ReLU fixes vanishing gradients in one sentence
- [ ] Your pure-Python network achieves >90% on a classification task
- [ ] You can modify the network depth/width and predict what will happen BEFORE running it

---

### WEEK 2 — "Go Deep Without Drowning"
**Core concept:** Depth is power, but only with the right engineering (init, norm, architecture).

**Curriculum points covered:**
- ③ Overparameterization helps
- ⑥ Geometry matters (loss landscapes)
- ⑦ Capacity ≠ performance

**Resources:**
| Resource | Why This One |
|----------|-------------|
| **PyTorch Official Tutorials: "60-Minute Blitz" (pytorch.org)** | Fastest way to get productive in PyTorch. Skip if you already know it. |
| **Dive into Deep Learning, Ch.5–6 (d2l.ai)** | Free interactive textbook. Best coverage of initialization, normalization, and regularization with runnable code. |
| **Andrej Karpathy: "A Recipe for Training Neural Networks" (blog post)** | The single best practical guide to debugging training. Print this out. |

**Build exercise:** Complete notebooks `W2_01` through `W2_02` (PyTorch series). You will:
1. Rebuild your Week 1 network in PyTorch (feel the difference)
2. Experiment with He/Xavier init, BatchNorm, Dropout
3. Visualize loss landscapes and compare flat vs sharp minima
4. Deliberately overfit, then fix it

**"You know you've got it when..."**
- [ ] You can take a model that's NOT training and systematically debug it
- [ ] You can explain overparameterization to a non-technical person
- [ ] Switching from SGD to Adam, you can predict the effect on training curves
- [ ] You've seen a loss landscape and can point to where generalization is better

---

### WEEK 3 — "Generate and Ship"
**Core concept:** Generative models learn data distributions; deployment is just engineering.

**Curriculum points covered:**
- All 7 points integrated into a capstone project
- Plus: Generative AI fundamentals (VAE, intro to Transformers)

**Resources:**
| Resource | Why This One |
|----------|-------------|
| **Lilian Weng: "From Autoencoder to Beta-VAE" (lilianweng.github.io)** | Best single-page explanation of generative model progression. Dense but worth it. |
| **Hugging Face Transformers Course, Ch.1 (huggingface.co/learn)** | Practical intro to using pre-trained models. You'll use this for deployment. |
| **Gradio Quickstart (gradio.app)** | Deploy a model as a web app in 10 lines of code. Fastest path to "full-stack." |

**Build exercise:** Complete notebooks `W3_01` through `W3_02` (both series). You will:
1. Build a Variational Autoencoder from scratch (pure Python), then in PyTorch
2. Generate new images from your trained VAE
3. Wrap your model in a Gradio app and deploy it

**"You know you've got it when..."**
- [ ] Your VAE generates recognizable (if blurry) new images
- [ ] You can explain the reparameterization trick
- [ ] Someone can open a URL and interact with your model
- [ ] You have a GitHub repo with README, notebooks, and deployed app link

---

## 3. PROJECTS LADDER

| # | Project | What It Proves | Builds On |
|---|---------|---------------|-----------|
| **P1** | Neural Network from Scratch | You understand the fundamentals, not just the API | Nothing — this is your foundation |
| **P2** | Image Classifier (PyTorch) | You can use modern tools and debug real training | P1's conceptual understanding |
| **P3** | Variational Autoencoder | You understand generative modeling | P2's PyTorch skills |
| **P4** | Deployed Generative App | You can ship, not just prototype | Everything above |

Each project is in the notebooks. P4 is the one you show people.

---

## 4. COMMON TRAPS (Top 5)

### Trap 1: "Tutorial Hell"
**What happens:** You watch 40 hours of courses and can't build anything.  
**Fix:** After each video/chapter, close it and rebuild what you saw WITHOUT looking. If you can't, you didn't learn it.

### Trap 2: "Framework Before Foundations"
**What happens:** You learn PyTorch syntax but can't debug because you don't know what backprop actually does.  
**Fix:** That's why Week 1 is pure Python. Suffer through it. It pays off in Week 2.

### Trap 3: "Hyperparameter Lottery"
**What happens:** You randomly try learning rates, architectures, and batch sizes hoping something works.  
**Fix:** Always change ONE thing at a time. Log everything. The notebooks enforce this with structured experiments.

### Trap 4: "Confusing Memorization with Learning"
**What happens:** Your training loss is 0.001 but test accuracy is 55%.  
**Fix:** ALWAYS hold out test data. Always plot train vs. val loss. The notebooks show you what overfitting looks like.

### Trap 5: "Skipping the Math (Entirely)"
**What happens:** You treat everything as a black box and hit a wall when things break.  
**Fix:** You don't need proofs, but you MUST understand: chain rule, gradient flow, what loss functions measure. The notebooks build this intuitively through code, not textbooks.

---

## 5. VALIDATION — Prove You've Learned This

### Portfolio Pieces (do all three):
1. **GitHub repo** with clean notebooks, a trained model, and a README that explains your approach
2. **Deployed app** (Gradio on Hugging Face Spaces — it's free)
3. **Blog post** walking through your "aha moments" (even a short one on Medium or dev.to)

### Certifications (optional, but credible):
- **DeepLearning.AI — "Deep Learning Specialization" Certificate** (Coursera) — industry-recognized
- **Hugging Face Certification** — practical and respected in the GenAI community

### Communities for Feedback:
- **r/MachineLearning** and **r/LearnMachineLearning** (Reddit)
- **Hugging Face Discord** — active, helpful, focused on builders
- **fast.ai Forums** — one of the best ML learning communities online
- **Weights & Biases Community** — great for sharing training experiments

---

## 6. TODAY'S ASSIGNMENT (30 minutes)

Open notebook `W1_01_Pure_Single_Neuron.ipynb` and complete it.

In 30 minutes you will:
1. Code a single neuron with sigmoid activation (5 min)
2. Replace sigmoid with ReLU and observe the difference (5 min)
3. Train it on a simple AND/OR gate with gradient descent (10 min)
4. Answer the challenge question: "Why can't a single neuron learn XOR?" (10 min)

**When you finish, you'll have written your first neural network. Not imported one. Written one.**

---

## NOTEBOOK INDEX

### Pure Python Series (NumPy only)
| File | Week | Topic |
|------|------|-------|
| `W1_01_Pure_Single_Neuron.ipynb` | 1 | Single neuron, activations, forward pass |
| `W1_02_Pure_Backprop_From_Scratch.ipynb` | 1 | Backpropagation, chain rule, gradient descent |
| `W1_03_Pure_Multi_Layer_Network.ipynb` | 1 | Full network, UAT demo, decision boundaries |
| `W3_01_Pure_Autoencoder.ipynb` | 3 | Autoencoder & VAE from scratch |

### PyTorch Series
| File | Week | Topic |
|------|------|-------|
| `W2_01_PyTorch_First_Network.ipynb` | 2 | PyTorch fundamentals, rebuilding Week 1 |
| `W2_02_PyTorch_Going_Deeper.ipynb` | 2 | Init, normalization, loss landscapes, overparameterization |
| `W3_02_PyTorch_Generative_AI.ipynb` | 3 | VAE in PyTorch, generation, latent space |
| `W3_03_PyTorch_Deploy_App.ipynb` | 3 | Wrap model in Gradio, deploy full-stack |

---

*"The best way to understand deep learning is to make a computer learn — and break — repeatedly."*
