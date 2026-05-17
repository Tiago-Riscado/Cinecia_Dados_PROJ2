"""
Diagnóstico de memória — testar se o dataset cabe em pandas com 32 GB RAM
Corre este script ANTES de tentar carregar o ficheiro todo.
"""

import os
import psutil
import pandas as pd
from dotenv import load_dotenv


# ── Configuração ────────────────────────────────────────────────────────────
load_dotenv()
DATA_PATH = os.getenv('CSV_PATH')   # ajusta o caminho

VALUE_COLS = [f'value{i}' for i in range(1, 32)]
USE_COLS   = ['id', 'year', 'month', 'element'] + VALUE_COLS
DTYPES = {
    'id':      'string',
    'year':    'int16',
    'month':   'int8',
    'element': 'string',
    **{col: 'Int16' for col in VALUE_COLS}
}


# ── 1. RAM disponível agora ──────────────────────────────────────────────────
ram = psutil.virtual_memory()
print("=" * 55)
print(f"  RAM total:       {ram.total  / 1024**3:.1f} GB")
print(f"  RAM disponível:  {ram.available / 1024**3:.1f} GB")
print(f"  RAM usada:       {ram.used   / 1024**3:.1f} GB  ({ram.percent}%)")
print("=" * 55)


# ── 2. Tamanho do ficheiro em disco ─────────────────────────────────────────
file_size_gb = os.path.getsize(DATA_PATH) / 1024**3
print(f"\nFicheiro em disco: {file_size_gb:.2f} GB")


# ── 3. Estimativa de memória via chunk de 100k linhas ───────────────────────
print("\nA ler chunk de 100 000 linhas para estimar uso de memória...")

chunk = pd.read_csv(
    DATA_PATH,
    usecols=USE_COLS,
    dtype=DTYPES,
    na_values=[-9999],
    nrows=100_000
)

chunk_mem_mb = chunk.memory_usage(deep=True).sum() / 1024**2
rows_per_mb  = 100_000 / chunk_mem_mb

# Estimar total de linhas pelo tamanho do ficheiro
# (assume ~proporção linear entre disco e linhas)
avg_row_bytes_disk = os.path.getsize(DATA_PATH) / max(1, sum(1 for _ in open(DATA_PATH)) - 1)
estimated_rows     = int(os.path.getsize(DATA_PATH) / avg_row_bytes_disk)
estimated_total_gb = (chunk_mem_mb / 100_000) * estimated_rows / 1024

print(f"\n  Memória do chunk (100k linhas): {chunk_mem_mb:.1f} MB")
print(f"  Linhas estimadas no ficheiro:   {estimated_rows:,}")
print(f"  Memória estimada (dataset completo, tipos otimizados): {estimated_total_gb:.1f} GB")


# ── 4. Veredicto ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
safety_margin = 0.75   # usar no máximo 75% da RAM disponível
ram_usable_gb = (ram.available / 1024**3) * safety_margin

print(f"  RAM utilizável com segurança (75%): {ram_usable_gb:.1f} GB")
print(f"  Memória estimada necessária:        {estimated_total_gb:.1f} GB")
print()

if estimated_total_gb < ram_usable_gb:
    print("  ✅ RESULTADO: Podes carregar o dataset inteiro com pd.read_csv()")
    print("     (com os dtypes otimizados definidos acima)")
else:
    print("  ⚠️  RESULTADO: Dataset demasiado grande — usa chunksize")
    recommended_chunk = int(ram_usable_gb * 1024 / chunk_mem_mb * 100_000 / 4)
    print(f"     Chunk recomendado: ~{recommended_chunk:,} linhas")
print("=" * 55)


# ── 5. (Opcional) Tentar carregar tudo e medir tempo real ────────────────────
resposta = input("\nQueres tentar carregar o ficheiro completo agora? (s/n): ").strip().lower()
if resposta == 's':
    import time
    print("A carregar... (pode demorar alguns minutos)")
    t0 = time.time()
    try:
        df_full = pd.read_csv(
            DATA_PATH,
            usecols=USE_COLS,
            dtype=DTYPES,
            na_values=[-9999]
        )
        elapsed = time.time() - t0
        mem_real = df_full.memory_usage(deep=True).sum() / 1024**3
        print(f"\n  ✅ Carregado com sucesso!")
        print(f"     Linhas: {len(df_full):,}")
        print(f"     Memória real: {mem_real:.2f} GB")
        print(f"     Tempo: {elapsed:.1f}s")
    except MemoryError:
        print("\n  ❌ MemoryError — RAM insuficiente. Usa chunksize.")
else:
    print("Ok. Usa o resultado da estimativa acima para decidir.")
