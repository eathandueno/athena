import torch 
import torch.nn as nn
from torch.nn import functional as F
import mmap
import random
import pickle 
import argparse

# parser = argparse.ArgumentParser(description='This is a demonstration program')
# parser.add_argument('-batch_size', type=str, required=True, help='Please provide a batch_size')
# args = parser.parse_args()
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(device)
block_size=64
batch_size=128
max_iters=1000
learning_rate= 3e-3
eval_iters=100
n_embd = 384
n_head = 8 # number of heads running in parallel
n_layer = 8 # number of decoder blocks
dropout = 0.2

chars = ""
with open('vocab.txt','r',encoding='utf-8') as f:
    text=f.read()
    chars = sorted(list(set(text)))
vocab_size = len(chars)

# Tokenizer
string_to_int = { ch:i for i,ch in enumerate(chars) }
int_to_string = { i:ch for i,ch in enumerate(chars) }
encode = lambda s: [string_to_int[c] for c in s]
decode = lambda l: ''.join([int_to_string[i] for i in l])


# hs = head size
class Head(nn.Module):
    """ one head of self-attention  """
    def __init__(self, head_size):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.register_buffer('tril', torch.tril(torch.ones(block_size, block_size)))
        
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # input of size (batch, time-step, channels)
        # output of size (batch, time-step, channels)
        B,T,C = x.shape
        k = self.key(x) # (B,T,hs)
        q = self.query(x) # (B,T,hs)
        # Compute attention scores ("affinities")
        wei = q @ k.transpose(-2,-1) * k.shape[-1]**-0.5 # (B,T,hs) @ (B,hs, T) -> (B,T,T)
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float('-inf')) # (B,T,T)
        wei = F.softmax(wei, dim=-1) # (B,T,T)
        wei = self.dropout(wei)
        # perform the weighted aggregation of the values
        v = self.value(x) # (B,T,hs) 
        out = wei @ v # (B,T,T) @ (B,T,hs) -> (B, T, hs)
        return out
        
        
    
class MultiHeadAttention(nn.Module):
    """ multiple heads of self-attention in parallel """
    def __init__(self, num_heads, head_size):
        super().__init__()
        self.heads = nn.ModuleList([Head(head_size) for _ in range(num_heads)])
        self.proj = nn.Linear(head_size * num_heads, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1) # (B, T, F) last dimension -> (B, T, [h1, h1, h1, h2, h2, h2])
        out = self.dropout(self.proj(out))
        return out
        
class FeedForward(nn.Module):
    """   a simple linear layer followed by a non-linearity  """
    def __init__(self, n_embd):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.ReLU(),
            nn.Linear(4 * n_embd, n_embd),
            nn.Dropout(dropout),
        )
        
    def forward(self, x):
        return self.net(x)
        
class Block(nn.Module):
    """ Transformer Block: communication followed by computation    """
    def __init__(self, n_embd, n_head):
        # n_embd: embedding dimension, n_head: the number of heads we'd like
        super().__init__()
        head_size = n_embd // n_head
        self.sa = MultiHeadAttention(n_head, head_size)
        self.ffwd = FeedForward(n_embd)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        # Self attention
        y=self.sa(x)
        # Add and norm
        x=self.ln1(x+y)
        # Feed forward
        y=self.ffwd(x)
        # Add and norm
        x=self.ln2(x+y)
        return x
        
class GPTLanguageModel(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        # Create a table with the dimensions of the vocab size each token is then mapped in the embedding vector
        self.token_embedding_table = nn.Embedding(vocab_size, n_embd) 
        self.position_embedding_table = nn.Embedding(block_size, n_embd)
        # Create N decoder layers
        self.blocks = nn.Sequential(*[Block(n_embd, n_head=n_head) for _ in range(n_layer)])
        # Help converge at the end
        self.ln_f = nn.LayerNorm(n_embd) # final layer norm
        # Language modeling head for final transformation
        self.lm_head = nn.Linear(n_embd, vocab_size)

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.2)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
    
    # Define forward pass of the neural network. Two parameters are taken index (input tokens) and targets (ground truth tokens: optional)
    def forward(self, index, targets=None):
        # Input is passed to table for init
        B,T = index.shape
        
        # idx and targets are both (B, T) tensor of integers
        tok_emb=self.token_embedding_table(index) # (B,T,C)
        pos_emb=self.position_embedding_table(torch.arange(T, device=device)) # (T,C)
        x=tok_emb + pos_emb # (B,T,C)
        x=self.blocks(x) # (B,T,C)
        x=self.ln_f(x) # (B,T,C)
        logits=self.lm_head(x) # (B, T , Vocab_size)
        
        if targets is None:
            loss = None
        else:
            # Cross entropy is calculated across the predicted logits and true targets
            B, T, C = logits.shape
            logits = logits.view(B*T, C)
            targets = targets.view(B*T)
            loss = F.cross_entropy(logits, targets)
        
        return logits, loss

    # Define a function to generate new tokens given a starting context
    def generate(self, index, max_new_tokens):
        # index is (B, T) array of indices in the current context
        # new tokens generated in loop appending to index tensor
        for _ in range(max_new_tokens):
            # crop idx to the last block_size tokens
            index_cond = index[:, -block_size:]
            # get the predictions
            logits, loss = self.forward(index_cond)
            # focus only on the last time step
            logits = logits[:,-1,:] # becomes (B, C)
            # Apply softmax to get probabilities 
            probs = F.softmax(logits, dim=-1) # (B, C)
            # sample from the distrubution
            index_next = torch.multinomial(probs, num_samples=1) # (B, 1)
            # Append sampled index to the running sequence
            index = torch.cat((index, index_next), dim=1) # (B, T+1)
        return index

model = GPTLanguageModel(vocab_size)
print('loading model parameters...')
with open('model-01.pk1', 'rb') as f:
    model = pickle.load(f)
print('loaded successfully')
m = model.to(device)

while True:
    prompt = input("Prompt: \n")
    context = torch.tensor(encode(prompt), dtype=torch.long, device=device)
    generated_chars = decode(m.generate(context.unsqueeze(0), max_new_tokens=150)[0].tolist())
    print(f"Completion:\n{generated_chars}")