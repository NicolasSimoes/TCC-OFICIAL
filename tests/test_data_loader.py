"""
Testes unitários para o módulo data_loader.py
"""

import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_loader import (
    normalize_header,
    mapear_colunas,
    validar_colunas_obrigatorias,
    limpar_coordenadas,
    limpar_classe_social
)


class TestNormalizeHeader(unittest.TestCase):
    """Testes para normalize_header"""
    
    def test_remove_acentos(self):
        """Testa remoção de acentos"""
        self.assertEqual(normalize_header("Público"), "PUBLICO")
        self.assertEqual(normalize_header("Descrição"), "DESCRICAO")
        self.assertEqual(normalize_header("Ação"), "ACAO")
    
    def test_uppercase(self):
        """Testa conversão para maiúsculas"""
        self.assertEqual(normalize_header("cliente"), "CLIENTE")
        self.assertEqual(normalize_header("Nome"), "NOME")
    
    def test_remove_espacos_duplos(self):
        """Testa remoção de espaços duplos"""
        self.assertEqual(normalize_header("NOME  COMPLETO"), "NOME COMPLETO")
    
    def test_substitui_caracteres(self):
        """Testa substituição de caracteres especiais"""
        self.assertEqual(normalize_header("NOME-COMPLETO"), "NOME COMPLETO")
        self.assertEqual(normalize_header("NOME/COMPLETO"), "NOME COMPLETO")
        self.assertEqual(normalize_header("NOME\\COMPLETO"), "NOME COMPLETO")
    
    def test_strip(self):
        """Testa remoção de espaços nas pontas"""
        self.assertEqual(normalize_header("  NOME  "), "NOME")


class TestMapearColunas(unittest.TestCase):
    """Testes para mapear_colunas"""
    
    def test_mapeia_cliente(self):
        """Testa mapeamento de coluna CLIENTE"""
        df = pd.DataFrame({"CLIENTE": [1, 2], "OUTRO": [3, 4]})
        df_mapped = mapear_colunas(df)
        self.assertIn("nome", df_mapped.columns)
        self.assertNotIn("CLIENTE", df_mapped.columns)
    
    def test_mapeia_coordenadas(self):
        """Testa mapeamento de coordenadas"""
        df = pd.DataFrame({
            "LATITUDE": [-3.7319],
            "LONGITUDE": [-38.5267]
        })
        df_mapped = mapear_colunas(df)
        self.assertIn("lat", df_mapped.columns)
        self.assertIn("lon", df_mapped.columns)
    
    def test_mapeia_classe_social(self):
        """Testa mapeamento de classe social"""
        df = pd.DataFrame({"CLASSE SOCIAL": ["A", "B"]})
        df_mapped = mapear_colunas(df)
        self.assertIn("classe", df_mapped.columns)
    
    def test_mantem_colunas_nao_mapeadas(self):
        """Testa que mantém colunas não mapeadas"""
        df = pd.DataFrame({
            "CLIENTE": [1],
            "COLUNA_QUALQUER": [2]
        })
        df_mapped = mapear_colunas(df)
        self.assertIn("COLUNA_QUALQUER", df_mapped.columns)
    
    def test_nao_quebra_sem_colunas(self):
        """Testa que não quebra com DataFrame vazio"""
        df = pd.DataFrame()
        df_mapped = mapear_colunas(df)
        self.assertIsInstance(df_mapped, pd.DataFrame)


class TestValidarColunasObrigatorias(unittest.TestCase):
    """Testes para validar_colunas_obrigatorias"""
    
    def test_valida_colunas_presentes(self):
        """Testa validação com todas colunas presentes"""
        df = pd.DataFrame({
            "nome": [1],
            "lat": [2],
            "lon": [3]
        })
        # Não deve lançar exceção
        try:
            validar_colunas_obrigatorias(df, ["nome", "lat", "lon"])
        except ValueError:
            self.fail("validar_colunas_obrigatorias lançou ValueError inesperadamente")
    
    def test_levanta_erro_coluna_faltando(self):
        """Testa erro quando coluna obrigatória falta"""
        df = pd.DataFrame({"nome": [1]})
        with self.assertRaises(ValueError) as context:
            validar_colunas_obrigatorias(df, ["nome", "lat"])
        
        self.assertIn("lat", str(context.exception))
    
    def test_levanta_erro_multiplas_colunas(self):
        """Testa erro com múltiplas colunas faltando"""
        df = pd.DataFrame({"nome": [1]})
        with self.assertRaises(ValueError):
            validar_colunas_obrigatorias(df, ["nome", "lat", "lon", "classe"])


class TestLimparCoordenadas(unittest.TestCase):
    """Testes para limpar_coordenadas"""
    
    def test_corrige_coordenadas_multiplicadas(self):
        """Testa correção de coordenadas multiplicadas por milhão"""
        df = pd.DataFrame({
            "lat": [-3731900.0],
            "lon": [-38526700.0]
        })
        df_limpo = limpar_coordenadas(df)
        
        self.assertAlmostEqual(df_limpo["lat"].iloc[0], -3.7319, places=4)
        self.assertAlmostEqual(df_limpo["lon"].iloc[0], -38.5267, places=4)
    
    def test_mantem_coordenadas_corretas(self):
        """Testa que mantém coordenadas já corretas"""
        df = pd.DataFrame({
            "lat": [-3.7319],
            "lon": [-38.5267]
        })
        df_limpo = limpar_coordenadas(df)
        
        self.assertAlmostEqual(df_limpo["lat"].iloc[0], -3.7319, places=4)
        self.assertAlmostEqual(df_limpo["lon"].iloc[0], -38.5267, places=4)
    
    def test_remove_coordenadas_invalidas(self):
        """Testa remoção de coordenadas inválidas"""
        df = pd.DataFrame({
            "lat": [-3.7319, None, -3.8],
            "lon": [-38.5267, -38.5, None]
        })
        df_limpo = limpar_coordenadas(df)
        
        self.assertEqual(len(df_limpo), 1)  # Apenas primeira linha é válida
    
    def test_converte_strings_para_float(self):
        """Testa conversão de strings para float"""
        df = pd.DataFrame({
            "lat": ["-3.7319"],
            "lon": ["-38.5267"]
        })
        df_limpo = limpar_coordenadas(df)
        
        self.assertAlmostEqual(df_limpo["lat"].iloc[0], -3.7319, places=4)


class TestLimparClasseSocial(unittest.TestCase):
    """Testes para limpar_classe_social"""
    
    def test_normaliza_classe(self):
        """Testa normalização de classe social"""
        df = pd.DataFrame({"classe": ["a", "B ", " c", "D", "e"]})
        df_limpo = limpar_classe_social(df)
        
        self.assertTrue(all(df_limpo["classe"].isin(["A", "B", "C", "D", "E"])))
    
    def test_remove_classes_invalidas(self):
        """Testa remoção de classes inválidas"""
        df = pd.DataFrame({"classe": ["A", "X", "B", "Z", "C"]})
        df_limpo = limpar_classe_social(df)
        
        self.assertEqual(len(df_limpo), 3)  # Apenas A, B, C
        self.assertTrue(all(df_limpo["classe"].isin(["A", "B", "C"])))
    
    def test_extrai_primeira_letra(self):
        """Testa extração da primeira letra"""
        df = pd.DataFrame({"classe": ["A1", "B2", "C3"]})
        df_limpo = limpar_classe_social(df)
        
        self.assertEqual(list(df_limpo["classe"]), ["A", "B", "C"])
    
    def test_nao_quebra_sem_coluna_classe(self):
        """Testa que não quebra se não houver coluna classe"""
        df = pd.DataFrame({"nome": ["teste"]})
        df_limpo = limpar_classe_social(df)
        
        self.assertIsInstance(df_limpo, pd.DataFrame)
        self.assertIn("nome", df_limpo.columns)


class TestIntegracaoDataLoader(unittest.TestCase):
    """Testes de integração do data_loader"""
    
    def test_pipeline_completo(self):
        """Testa pipeline completo de limpeza"""
        # Cria DataFrame "sujo"
        df = pd.DataFrame({
            "CLIENTE": ["Cliente A", "Cliente B"],
            "LATITUDE": [-3731900.0, -3741900.0],
            "LONGITUDE": [-38526700.0, -38516700.0],
            "CLASSE SOCIAL": ["a", "B "],
            "TIPO COMERCIAL": ["Mercado", "Farmácia"]
        })
        
        # Aplica transformações
        df = mapear_colunas(df)
        df = limpar_coordenadas(df)
        df = limpar_classe_social(df)
        
        # Valida resultado
        self.assertIn("nome", df.columns)
        self.assertIn("lat", df.columns)
        self.assertIn("lon", df.columns)
        self.assertIn("classe", df.columns)
        
        self.assertEqual(len(df), 2)
        self.assertTrue(all(df["classe"].isin(["A", "B"])))
        self.assertTrue(all(df["lat"] < 0))
        self.assertTrue(all(df["lat"] > -10))


if __name__ == "__main__":
    unittest.main()
