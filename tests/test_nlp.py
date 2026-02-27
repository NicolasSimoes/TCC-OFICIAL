"""
Testes unitários para o módulo nlp.py
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nlp import (
    identificar_nicho,
    sugerir_pois_para_nicho,
    sugerir_pesos_classe,
    analisar_produto_completo,
    gerar_estrategia_comercial
)


class TestIdentificarNicho(unittest.TestCase):
    """Testes para a função identificar_nicho"""
    
    def test_nicho_fitness(self):
        """Testa identificação de produtos fitness"""
        self.assertEqual(identificar_nicho("whey protein"), "Fitness")
        self.assertEqual(identificar_nicho("creatina monohidratada"), "Fitness")
        self.assertEqual(identificar_nicho("suplemento de academia"), "Fitness")
    
    def test_nicho_infantil(self):
        """Testa identificação de produtos infantis"""
        self.assertEqual(identificar_nicho("fralda descartável"), "Infantil")
        self.assertEqual(identificar_nicho("mamadeira bebê"), "Infantil")
        self.assertEqual(identificar_nicho("papinha nestlé"), "Infantil")
    
    def test_nicho_escolar(self):
        """Testa identificação de produtos escolares"""
        self.assertEqual(identificar_nicho("caderno universitário"), "Escolar")
        self.assertEqual(identificar_nicho("mochila escolar"), "Escolar")
        self.assertEqual(identificar_nicho("lápis e caneta"), "Escolar")
    
    def test_nicho_alimentacao(self):
        """Testa identificação de produtos de alimentação"""
        self.assertEqual(identificar_nicho("biscoito chocolate"), "Alimentação")
        self.assertEqual(identificar_nicho("refrigerante coca"), "Alimentação")
        self.assertEqual(identificar_nicho("suco natural"), "Alimentação")
    
    def test_nicho_farmacia(self):
        """Testa identificação de produtos farmacêuticos"""
        self.assertEqual(identificar_nicho("remédio dor de cabeça"), "Farmácia")
        self.assertEqual(identificar_nicho("vitamina C"), "Farmácia")
        self.assertEqual(identificar_nicho("antibiótico"), "Farmácia")
    
    def test_nicho_beleza(self):
        """Testa identificação de produtos de beleza"""
        self.assertEqual(identificar_nicho("shampoo cabelo"), "Beleza")
        self.assertEqual(identificar_nicho("perfume importado"), "Beleza")
        self.assertEqual(identificar_nicho("creme hidratante"), "Beleza")
    
    def test_nicho_pet(self):
        """Testa identificação de produtos pet"""
        self.assertEqual(identificar_nicho("ração para cachorro"), "Pet")
        self.assertEqual(identificar_nicho("brinquedo pet gato"), "Pet")
        self.assertEqual(identificar_nicho("coleira"), "Pet")
    
    def test_nicho_eletronicos(self):
        """Testa identificação de eletrônicos"""
        self.assertEqual(identificar_nicho("fone bluetooth"), "Eletrônicos")
        self.assertEqual(identificar_nicho("smartphone samsung"), "Eletrônicos")
        self.assertEqual(identificar_nicho("carregador celular"), "Eletrônicos")
    
    def test_texto_vazio(self):
        """Testa comportamento com texto vazio"""
        self.assertEqual(identificar_nicho(""), "Outro")
        self.assertEqual(identificar_nicho(None), "Outro")
        self.assertEqual(identificar_nicho("   "), "Outro")
    
    def test_produto_desconhecido(self):
        """Testa produto que não se encaixa em nenhum nicho"""
        self.assertEqual(identificar_nicho("produto xyz abc 123"), "Outro")
    
    def test_case_insensitive(self):
        """Testa que a função é case insensitive"""
        self.assertEqual(identificar_nicho("WHEY PROTEIN"), "Fitness")
        self.assertEqual(identificar_nicho("Whey Protein"), "Fitness")
        self.assertEqual(identificar_nicho("whey protein"), "Fitness")


class TestSugerirPoisParaNicho(unittest.TestCase):
    """Testes para sugerir_pois_para_nicho"""
    
    def test_pois_fitness(self):
        """Testa POIs para nicho Fitness"""
        pois = sugerir_pois_para_nicho("Fitness")
        self.assertIn("gym", pois)
        self.assertIn("health", pois)
        self.assertIsInstance(pois, list)
        self.assertGreater(len(pois), 0)
    
    def test_pois_infantil(self):
        """Testa POIs para nicho Infantil"""
        pois = sugerir_pois_para_nicho("Infantil")
        self.assertIn("school", pois)
        self.assertIn("park", pois)
    
    def test_pois_desconhecido(self):
        """Testa POIs para nicho desconhecido"""
        pois = sugerir_pois_para_nicho("Outro")
        self.assertIsInstance(pois, list)
        self.assertGreater(len(pois), 0)
    
    def test_retorna_lista(self):
        """Testa que sempre retorna uma lista"""
        for nicho in ["Fitness", "Infantil", "Escolar", "Outro"]:
            pois = sugerir_pois_para_nicho(nicho)
            self.assertIsInstance(pois, list)


class TestSugerirPesosClasse(unittest.TestCase):
    """Testes para sugerir_pesos_classe"""
    
    def test_pesos_fitness(self):
        """Testa pesos para nicho Fitness (foco classe alta)"""
        pesos = sugerir_pesos_classe("Fitness")
        self.assertGreater(pesos["A"], pesos["C"])
        self.assertIn("A", pesos)
        self.assertIn("B", pesos)
        self.assertIn("C", pesos)
    
    def test_pesos_escolar(self):
        """Testa pesos para nicho Escolar (foco classe média)"""
        pesos = sugerir_pesos_classe("Escolar")
        self.assertGreaterEqual(pesos["B"], pesos["A"])
    
    def test_estrutura_retorno(self):
        """Testa estrutura do dicionário retornado"""
        pesos = sugerir_pesos_classe("Fitness")
        self.assertIsInstance(pesos, dict)
        self.assertIn("A", pesos)
        self.assertIn("B", pesos)
        self.assertIn("C", pesos)
    
    def test_valores_positivos(self):
        """Testa que todos os pesos são positivos"""
        for nicho in ["Fitness", "Infantil", "Escolar", "Outro"]:
            pesos = sugerir_pesos_classe(nicho)
            for peso in pesos.values():
                self.assertGreater(peso, 0)


class TestAnalisarProdutoCompleto(unittest.TestCase):
    """Testes para analisar_produto_completo"""
    
    def test_analise_completa(self):
        """Testa análise completa de produto"""
        resultado = analisar_produto_completo("whey protein")
        
        self.assertIn("nicho", resultado)
        self.assertIn("pois_sugeridos", resultado)
        self.assertIn("pesos_classe", resultado)
        self.assertIn("descricao", resultado)
        
        self.assertEqual(resultado["nicho"], "Fitness")
        self.assertIsInstance(resultado["pois_sugeridos"], list)
        self.assertIsInstance(resultado["pesos_classe"], dict)
    
    def test_diferentes_produtos(self):
        """Testa análise de diferentes produtos"""
        produtos = [
            ("fralda pampers", "Infantil"),
            ("caderno 10 matérias", "Escolar"),
            ("shampoo dove", "Beleza")
        ]
        
        for produto, nicho_esperado in produtos:
            resultado = analisar_produto_completo(produto)
            self.assertEqual(resultado["nicho"], nicho_esperado)
    
    def test_integridade_dados(self):
        """Testa integridade dos dados retornados"""
        resultado = analisar_produto_completo("ração para cachorro")
        
        # Verifica que POIs e pesos são consistentes com o nicho
        self.assertEqual(resultado["nicho"], "Pet")
        self.assertGreater(len(resultado["pois_sugeridos"]), 0)
        self.assertGreater(len(resultado["pesos_classe"]), 0)


class TestGerarEstrategiaComercial(unittest.TestCase):
    """Testes para gerar_estrategia_comercial"""
    
    def test_estrategia_sem_openai(self):
        """Testa geração de estratégia sem OpenAI (fallback)"""
        regioes = [
            (-3.7319, -38.5267, "Aldeota"),
            (-3.7419, -38.5167, "Meireles")
        ]
        pesos = {"A": 50000, "B": 30000, "C": 10000}
        
        estrategia = gerar_estrategia_comercial(
            produto="whey protein",
            nicho="Fitness",
            regioes=regioes,
            pesos_classe=pesos
        )
        
        self.assertIsInstance(estrategia, str)
        self.assertGreater(len(estrategia), 100)
        self.assertIn("Fitness", estrategia)
    
    def test_estrategia_com_openai_mock(self):
        """Testa geração de estratégia com OpenAI (mockado)"""
        # Pula teste se OpenAI não estiver instalada
        try:
            from openai import OpenAI
        except ImportError:
            self.skipTest("OpenAI não instalada")
        
        with patch('nlp.OPENAI_AVAILABLE', True), \
             patch('nlp.OPENAI_API_KEY', 'fake-key'), \
             patch('nlp.OpenAI') as mock_openai:
            
            # Mock da resposta da OpenAI
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Estratégia gerada pela IA"
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            regioes = [(-3.7319, -38.5267, "Aldeota")]
            pesos = {"A": 50000, "B": 30000, "C": 10000}
            
            estrategia = gerar_estrategia_comercial(
                produto="whey protein",
                nicho="Fitness",
                regioes=regioes,
                pesos_classe=pesos
            )
            
            self.assertEqual(estrategia, "Estratégia gerada pela IA")
            mock_client.chat.completions.create.assert_called_once()
    
    def test_estrategia_sem_regioes(self):
        """Testa estratégia quando não há regiões"""
        estrategia = gerar_estrategia_comercial(
            produto="produto teste",
            nicho="Outro",
            regioes=[],
            pesos_classe={"A": 30000, "B": 20000, "C": 10000}
        )
        
        self.assertIsInstance(estrategia, str)
        self.assertGreater(len(estrategia), 0)
    
    def test_estrategia_com_filtros(self):
        """Testa estratégia com filtros aplicados"""
        estrategia = gerar_estrategia_comercial(
            produto="whey protein",
            nicho="Fitness",
            regioes=[(-3.7319, -38.5267, "Aldeota")],
            pesos_classe={"A": 50000, "B": 30000, "C": 10000},
            filtros={"classe": ["A", "B"], "tipo": "ACADEMIA", "bairro": ["Aldeota"]}
        )
        
        self.assertIsInstance(estrategia, str)


if __name__ == "__main__":
    unittest.main()
