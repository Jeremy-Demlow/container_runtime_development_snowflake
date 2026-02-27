"""
Example 2: GPU Embedding Job

Runs sentence embedding using sentence-transformers on GPU.

Run:
    python examples/02_gpu_embedding.py
"""

import tempfile
from sfml.jobs import submit_file

script_content = '''
import torch
from sentence_transformers import SentenceTransformer

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

if torch.cuda.is_available():
    model = model.to("cuda")
    print("Model moved to GPU")

texts = [
    "Machine learning on Snowflake",
    "GPU-accelerated embeddings",
    "Distributed computing with Ray",
    "Hello world from ML Jobs",
]

print(f"Encoding {len(texts)} texts...")
embeddings = model.encode(texts, show_progress_bar=True)

print(f"Embeddings shape: {embeddings.shape}")
print(f"First embedding (first 5 dims): {embeddings[0][:5]}")

print("\\nDone!")
'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(script_content)
    script_path = f.name

print("Submitting GPU embedding job...")
print("(This requires a GPU compute pool)")
print()

result = submit_file(
    script_path,
    compute_pool="GPU_POOL",
    pip_requirements=["torch", "sentence-transformers"],
    wait=True,
)

print(f"\nJob ID: {result['job_id']}")
print(f"Status: {result['status']}")
