import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gradio as gr

# --- VAE Model Definition ---
class VAE(nn.Module):
    def __init__(self, input_dim=64, hidden_dim=128, latent_dim=2):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU())
        self.fc_mu = nn.Linear(hidden_dim // 2, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim // 2, latent_dim)
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim // 2), nn.ReLU(),
            nn.Linear(hidden_dim // 2, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim), nn.Sigmoid())
    def decode(self, z): return self.decoder(z)

model = VAE()
model.load_state_dict(torch.load("vae_model.pth", map_location="cpu"))
model.eval()

def generate_digits(z1, z2, n_samples):
    fig, axes = plt.subplots(1, max(1,int(n_samples)), figsize=(2*n_samples,2))
    if n_samples == 1: axes = [axes]
    for i, ax in enumerate(axes):
        z = torch.FloatTensor([[z1, z2]]) if i == 0 else torch.randn(1, 2)
        with torch.no_grad(): gen = model.decode(z).numpy().reshape(8, 8)
        ax.imshow(gen, cmap='gray_r', vmin=0, vmax=1); ax.axis('off')
    plt.tight_layout()
    return fig

demo = gr.Interface(fn=generate_digits,
    inputs=[gr.Slider(-3,3,value=0,label='z1'),
            gr.Slider(-3,3,value=0,label='z2'),
            gr.Slider(1,8,value=4,step=1,label='Samples')],
    outputs=gr.Plot(), title='VAE Digit Generator')
demo.launch()