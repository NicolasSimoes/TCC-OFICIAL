"""
Utilitários para carregamento e normalização de dados.
Suporta múltiplos formatos (CSV, Excel) com normalização automática.
"""

import pandas as pd
import unicodedata
from pathlib import Path
from typing import Optional, Dict, List


def normalize_header(s: str) -> str:
    """
    Normaliza cabeçalhos de colunas removendo acentos e padronizando formato.
    
    Args:
        s: Nome da coluna
        
    Returns:
        Nome normalizado
    """
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    s = s.strip().upper().replace("  ", " ")
    s = s.replace("-", " ").replace("/", " ").replace("\\", " ")
    return s


def carregar_dados(caminho: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Carrega dados de CSV ou Excel com detecção automática de formato.
    Normaliza cabeçalhos automaticamente.
    
    Args:
        caminho: Caminho para o arquivo
        sheet_name: Nome da planilha (apenas para Excel)
        
    Returns:
        DataFrame com dados carregados e normalizados
        
    Raises:
        FileNotFoundError: Se arquivo não existir
        ValueError: Se formato não for suportado
    """
    path = Path(caminho)
    
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    
    # Detecta formato pelo extensão
    ext = path.suffix.lower()
    
    try:
        if ext == '.csv':
            # Tenta detectar separador automaticamente
            df = pd.read_csv(caminho, sep=None, engine="python", encoding="utf-8-sig")
        elif ext in ['.xlsx', '.xls']:
            if sheet_name:
                df = pd.read_excel(caminho, sheet_name=sheet_name)
            else:
                # Tenta carregar a primeira planilha
                df = pd.read_excel(caminho)
        else:
            raise ValueError(f"Formato não suportado: {ext}. Use .csv, .xlsx ou .xls")
        
        # Normaliza cabeçalhos
        df.columns = [normalize_header(c) for c in df.columns]
        
        return df
        
    except Exception as e:
        raise Exception(f"Erro ao carregar {caminho}: {str(e)}")


def mapear_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mapeia colunas comuns para nomes padronizados do sistema.
    
    Args:
        df: DataFrame original
        
    Returns:
        DataFrame com colunas renomeadas
    """
    # Mapa de aliases para nomes padronizados
    alias_map = {
        "CLIENTE": "nome",
        "NOME": "nome",
        "NOME DO CLIENTE": "nome",
        "RAZAO SOCIAL": "nome",
        
        "REDE": "rede",
        "BANDEIRA": "rede",
        
        "LAT": "lat",
        "LATITUDE": "lat",
        
        "LON": "lon",
        "LONG": "lon", 
        "LONGITUDE": "lon",
        
        "CLASSE SOCIAL": "classe",
        "CLASSE_SOCIAL": "classe",
        "CLASSE": "classe",
        
        "TIPO COMERCIAL": "tipo_comercial",
        "TIPO_COMERCIAL": "tipo_comercial",
        "TIPO": "tipo_comercial",
        "CATEGORIA": "tipo_comercial",
        
        "BAIRRO": "bairro",
        "NEIGHBORHOOD": "bairro",
        
        "CIDADE": "cidade",
        "MUNICIPIO": "cidade",
        "CITY": "cidade",
        
        "PONTOS DE INTERESSE": "pois_texto",
        "POI": "pois_texto",
    }
    
    # Renomeia apenas colunas que existem
    rename_dict = {col: alias_map[col] for col in df.columns if col in alias_map}
    df = df.rename(columns=rename_dict)
    
    return df


def validar_colunas_obrigatorias(df: pd.DataFrame, colunas: List[str]) -> None:
    """
    Valida se DataFrame possui colunas obrigatórias.
    
    Args:
        df: DataFrame a validar
        colunas: Lista de colunas obrigatórias
        
    Raises:
        ValueError: Se alguma coluna obrigatória estiver faltando
    """
    missing = [c for c in colunas if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {missing}\n"
            f"Colunas disponíveis: {list(df.columns)}"
        )


def limpar_coordenadas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e normaliza coordenadas geográficas.
    Corrige coordenadas multiplicadas por 1.000.000.
    
    Args:
        df: DataFrame com colunas 'lat' e 'lon'
        
    Returns:
        DataFrame com coordenadas corrigidas
    """
    df = df.copy()
    
    def fix_coord(v):
        try:
            v = float(v)
            # Se coordenada parece estar multiplicada por milhão
            if abs(v) > 1000:
                return v / 1_000_000
            return v
        except (ValueError, TypeError):
            return None
    
    if 'lat' in df.columns:
        df['lat'] = df['lat'].apply(fix_coord)
    
    if 'lon' in df.columns:
        df['lon'] = df['lon'].apply(fix_coord)
    
    # Remove linhas com coordenadas inválidas
    df = df.dropna(subset=['lat', 'lon'])
    
    return df


def limpar_classe_social(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza coluna de classe social para apenas letra maiúscula.
    
    Args:
        df: DataFrame com coluna 'classe'
        
    Returns:
        DataFrame com classe normalizada
    """
    if 'classe' not in df.columns:
        return df
    
    df = df.copy()
    df['classe'] = df['classe'].astype(str).str.strip().str.upper().str[0]
    # Mantém apenas classes válidas (A, B, C, D, E)
    df = df[df['classe'].isin(['A', 'B', 'C', 'D', 'E'])]
    
    return df


def carregar_e_preparar_dados(
    caminho: str,
    sheet_name: Optional[str] = "BASE",
    colunas_obrigatorias: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Pipeline completo de carregamento e preparação de dados.
    
    Args:
        caminho: Caminho para arquivo CSV ou Excel
        sheet_name: Nome da planilha (Excel)
        colunas_obrigatorias: Lista de colunas que devem existir
        
    Returns:
        DataFrame limpo e pronto para uso
    """
    if colunas_obrigatorias is None:
        colunas_obrigatorias = ['nome', 'lat', 'lon', 'classe', 'tipo_comercial']
    
    # 1. Carrega dados
    df = carregar_dados(caminho, sheet_name)
    
    # 2. Mapeia colunas
    df = mapear_colunas(df)
    
    # 3. Valida colunas obrigatórias
    validar_colunas_obrigatorias(df, colunas_obrigatorias)
    
    # 4. Limpa coordenadas
    df = limpar_coordenadas(df)
    
    # 5. Limpa classe social
    df = limpar_classe_social(df)
    
    # 6. Remove duplicatas
    df = df.drop_duplicates(subset=['nome', 'lat', 'lon'])
    
    # 7. Reseta índice
    df = df.reset_index(drop=True)
    
    print(f"✓ Dados carregados: {len(df)} registros válidos")
    print(f"  Colunas: {list(df.columns)}")
    
    return df
