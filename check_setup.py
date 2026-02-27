"""
Script de verificação e teste do ambiente Smart Sale Fortaleza.
Execute este script para validar a instalação e configuração.
"""

import sys
from pathlib import Path

def check_python_version():
    """Verifica versão do Python."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detectado. Requer Python 3.8+")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Verifica se dependências essenciais estão instaladas."""
    required = {
        'pandas': 'Manipulação de dados',
        'numpy': 'Computação numérica',
        'sklearn': 'Machine Learning',
        'folium': 'Mapas interativos',
        'streamlit': 'Interface web',
        'requests': 'HTTP requests',
        'dotenv': 'Variáveis de ambiente'
    }
    
    missing = []
    for module, desc in required.items():
        try:
            __import__(module)
            print(f"✓ {module:12} - {desc}")
        except ImportError:
            print(f"❌ {module:12} - {desc} (FALTANDO)")
            missing.append(module)
    
    return len(missing) == 0, missing


def check_env_file():
    """Verifica existência e conteúdo do arquivo .env."""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("⚠️  Arquivo .env não encontrado!")
        print("   Crie a partir do .env.example:")
        print("   cp .env.example .env")
        return False
    
    print("✓ Arquivo .env existe")
    
    # Verifica conteúdo
    with open(env_path) as f:
        content = f.read()
    
    if 'GOOGLE_API_KEY' not in content:
        print("⚠️  GOOGLE_API_KEY não encontrada no .env")
        return False
    
    if 'your_google_api_key_here' in content:
        print("⚠️  GOOGLE_API_KEY ainda não foi configurada")
        print("   Edite o arquivo .env e adicione sua chave da API")
        return False
    
    print("✓ GOOGLE_API_KEY configurada")
    return True


def check_data_files():
    """Verifica existência de arquivos de dados."""
    data_dir = Path('data')
    
    if not data_dir.exists():
        print("❌ Diretório 'data/' não encontrado")
        return False
    
    print("✓ Diretório 'data/' existe")
    
    # Procura por arquivos de dados
    excel_files = list(data_dir.glob('*.xlsx'))
    csv_files = list(data_dir.glob('*.csv'))
    
    if not excel_files and not csv_files:
        print("⚠️  Nenhum arquivo de dados (.xlsx ou .csv) encontrado em data/")
        return False
    
    for f in excel_files:
        print(f"  ✓ {f.name}")
    for f in csv_files:
        print(f"  ✓ {f.name}")
    
    return True


def check_src_structure():
    """Verifica estrutura de arquivos do src/."""
    src_dir = Path('src')
    
    required_files = [
        'main.py',
        'nlp.py',
        'clustering_pipeline.py',
        'map.py',
        'interface.py',
        'data_loader.py',
        'visualizations.py'
    ]
    
    if not src_dir.exists():
        print("❌ Diretório 'src/' não encontrado")
        return False
    
    print("✓ Diretório 'src/' existe")
    
    all_ok = True
    for filename in required_files:
        filepath = src_dir / filename
        if filepath.exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ❌ {filename} (FALTANDO)")
            all_ok = False
    
    return all_ok


def test_imports():
    """Testa imports dos módulos principais."""
    print("\n🧪 Testando imports dos módulos...")
    
    # Adiciona src ao path
    src_path = Path('src').absolute()
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    modules = ['nlp', 'data_loader', 'clustering_pipeline']
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name}")
        except Exception as e:
            print(f"  ❌ {module_name}: {str(e)}")
            return False
    
    return True


def test_nlp():
    """Testa funcionalidade básica do NLP."""
    print("\n🧪 Testando análise de produto...")
    
    try:
        from nlp import identificar_nicho, analisar_produto_completo
        
        # Teste 1: Identificação básica
        nicho = identificar_nicho("whey protein")
        assert nicho == "Fitness", f"Esperado 'Fitness', obteve '{nicho}'"
        print("  ✓ Identificação de nicho: Fitness")
        
        # Teste 2: Análise completa
        analise = analisar_produto_completo("fraldas pampers")
        assert analise['nicho'] == "Infantil", f"Esperado 'Infantil', obteve '{analise['nicho']}'"
        assert 'pois_sugeridos' in analise
        assert 'pesos_classe' in analise
        print("  ✓ Análise completa: Infantil")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro: {str(e)}")
        return False


def main():
    """Executa todas as verificações."""
    print("="*60)
    print("🔍 VERIFICAÇÃO DO AMBIENTE - Smart Sale Fortaleza")
    print("="*60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependências", lambda: check_dependencies()[0]),
        ("Arquivo .env", check_env_file),
        ("Arquivos de Dados", check_data_files),
        ("Estrutura src/", check_src_structure),
        ("Imports", test_imports),
        ("NLP", test_nlp),
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n📋 {name}")
        print("-" * 60)
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")
            results.append((name, False))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ OK" if result else "❌ FALHOU"
        print(f"{status:12} {name}")
    
    print(f"\n{'='*60}")
    print(f"Resultado: {passed}/{total} verificações passaram")
    print("="*60)
    
    if passed == total:
        print("\n🎉 Tudo certo! O ambiente está pronto para uso.")
        print("\n▶️  Para iniciar a aplicação:")
        print("   streamlit run src/interface.py")
    else:
        print("\n⚠️  Algumas verificações falharam.")
        print("   Revise os erros acima e corrija antes de continuar.")
        
        # Sugestões de correção
        if not any(r for n, r in results if n == "Dependências"):
            print("\n💡 Instale as dependências:")
            print("   pip install -r requirements.txt")
        
        if not any(r for n, r in results if n == "Arquivo .env"):
            print("\n💡 Configure o arquivo .env:")
            print("   1. cp .env.example .env")
            print("   2. Edite .env e adicione sua GOOGLE_API_KEY")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
