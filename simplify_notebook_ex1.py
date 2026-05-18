import json
from pathlib import Path


path = Path("src/notebook.ipynb")
nb = json.loads(path.read_text(encoding="utf-8"))


def source(text):
    return [line + "\n" for line in text.strip("\n").split("\n")]


nb["cells"][5]["source"] = source(
    """
year_parts = []

reader = pd.read_csv(
    DATA_PATH,
    usecols=['id', 'year'],
    dtype={'id': 'string', 'year': 'int16'},
    chunksize=CHUNK_SIZE
)

for ck in reader:
    year_parts.append(
        ck.groupby('id')['year'].agg(['min', 'max']).reset_index()
    )

station_years = (
    pd.concat(year_parts)
    .groupby('id')
    .agg(
        ano_mais_antigo=('min', 'min'),
        ano_mais_recente=('max', 'max')
    )
    .reset_index()
)

print(f"Total de estações: {len(station_years)}")
station_years.head(10)
"""
)

nb["cells"][9]["source"] = source(
    """
# Ler metadata das estações para associar cada id ao nome da estação
stations_path = STATIONS_PATH
if not os.path.exists(stations_path):
    alt_path = os.path.splitext(stations_path)[0] + '.txt'
    if os.path.exists(alt_path):
        stations_path = alt_path
    else:
        raise FileNotFoundError(
            f"Stations file not found: {stations_path!r}. "
            f"Verify STATIONS_PATH or put the file in the data folder."
        )

stations = pd.read_fwf(
    stations_path,
    colspecs=[(0, 11), (12, 20), (21, 30), (31, 37), (38, 40), (41, 71)],
    names=['id', 'lat', 'lon', 'elev', 'state', 'name'],
    dtype={'id': 'string', 'name': 'string'}
)
stations['name'] = stations['name'].str.strip()
stations['name_upper'] = stations['name'].str.upper()

agg_parts = []
reader_group = pd.read_csv(
    DATA_PATH,
    usecols=USE_COLS,
    dtype=DTYPES,
    na_values=[-9999],
    chunksize=CHUNK_SIZE
)

for ck in reader_group:
    ck['daily_avg_temp'] = ck[VALUE_COLS].mean(axis=1)
    agg_parts.append(
        ck.groupby(['id', 'year'])['daily_avg_temp']
        .agg(['sum', 'count'])
        .reset_index()
    )

station_year_agg = (
    pd.concat(agg_parts, ignore_index=True)
    .groupby(['id', 'year'])[['sum', 'count']]
    .sum()
    .reset_index()
    .merge(stations[['id', 'name']], on='id', how='left')
)

name_year_agg = (
    station_year_agg
    .groupby(['name', 'year'])[['sum', 'count']]
    .sum()
    .reset_index()
)
name_year_agg['daily_avg_temp'] = (name_year_agg['sum'] / name_year_agg['count']).round(2)

temp_by_station_year = name_year_agg[['name', 'year', 'daily_avg_temp']]

print("Temperatura media anual por nome da estação:")
temp_by_station_year.head(15)
"""
)

nb["cells"][11]["source"] = source(
    """
PT_TERMS = ['HORTA', 'FUNCHAL', 'LISBOA', 'CASTELO BRANCO', 'FARO']

pt_candidates = stations[
    stations['name_upper'].str.contains('|'.join(PT_TERMS), na=False)
][['id', 'name', 'lat', 'lon', 'elev']]

print("Candidatos encontrados no ficheiro de estações:")
print(pt_candidates)

selected = []
for term in PT_TERMS:
    matches = stations[stations['name_upper'].str.contains(term, na=False)]
    if not matches.empty:
        selected.append(matches.iloc[0])
    else:
        print(f"Aviso: não foi encontrada estação para {term}")

pt_stations = pd.DataFrame(selected).drop_duplicates(subset='id')
PT_IDS = pt_stations['id'].tolist()

print("\\nEstações portuguesas selecionadas:")
pt_stations[['id', 'name']]
"""
)

path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
