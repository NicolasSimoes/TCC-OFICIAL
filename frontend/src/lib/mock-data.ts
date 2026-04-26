import { AnalysisResult, Region, ActionItem, Strategy, Demographics } from '@/types';

// Bairros de Fortaleza com coordenadas reais
const fortalezaNeighborhoods: { name: string; lat: number; lng: number }[] = [
  { name: 'Aldeota', lat: -3.7356, lng: -38.5044 },
  { name: 'Meireles', lat: -3.7247, lng: -38.4989 },
  { name: 'Cocó', lat: -3.7450, lng: -38.4789 },
  { name: 'Papicu', lat: -3.7389, lng: -38.4845 },
  { name: 'Dionísio Torres', lat: -3.7489, lng: -38.5067 },
  { name: 'Fátima', lat: -3.7567, lng: -38.5278 },
  { name: 'Benfica', lat: -3.7478, lng: -38.5389 },
  { name: 'Centro', lat: -3.7278, lng: -38.5267 },
  { name: 'Praia de Iracema', lat: -3.7189, lng: -38.5156 },
  { name: 'Varjota', lat: -3.7312, lng: -38.4912 },
  { name: 'Mucuripe', lat: -3.7234, lng: -38.4834 },
  { name: 'Edson Queiroz', lat: -3.7689, lng: -38.4678 },
  { name: 'Messejana', lat: -3.8289, lng: -38.4934 },
  { name: 'Parangaba', lat: -3.7734, lng: -38.5623 },
  { name: 'Montese', lat: -3.7656, lng: -38.5456 },
  { name: 'Parquelândia', lat: -3.7412, lng: -38.5512 },
  { name: 'Joaquim Távora', lat: -3.7523, lng: -38.5134 },
  { name: 'São João do Tauape', lat: -3.7612, lng: -38.5034 },
  { name: 'Cidade dos Funcionários', lat: -3.7834, lng: -38.4867 },
  { name: 'Luciano Cavalcante', lat: -3.7634, lng: -38.4712 },
  { name: 'Guararapes', lat: -3.7556, lng: -38.4645 },
  { name: 'Salinas', lat: -3.7478, lng: -38.4589 },
  { name: 'Cambeba', lat: -3.7867, lng: -38.4789 },
  { name: 'José de Alencar', lat: -3.7978, lng: -38.4856 },
  { name: 'Passaré', lat: -3.8056, lng: -38.5234 },
  { name: 'Aerolândia', lat: -3.7789, lng: -38.5178 },
  { name: 'Jacarecanga', lat: -3.7234, lng: -38.5434 },
  { name: 'Pirambu', lat: -3.7156, lng: -38.5378 },
  { name: 'Barra do Ceará', lat: -3.7045, lng: -38.5589 },
  { name: 'Carlito Pamplona', lat: -3.7178, lng: -38.5523 },
];

const commercialTypes = ['Varejo', 'Serviços', 'Alimentação', 'Saúde', 'Educação', 'Tecnologia'];
const socialClasses: Array<'A' | 'B' | 'C' | 'D' | 'E'> = ['A', 'B', 'C', 'D', 'E'];

// Mapeamento de produtos para nichos
const productToNiche: { [key: string]: string } = {
  'cafeteria': 'Alimentação',
  'café': 'Alimentação',
  'coffee': 'Alimentação',
  'hamburgueria': 'Alimentação',
  'hamburguer': 'Alimentação',
  'restaurante': 'Alimentação',
  'pizzaria': 'Alimentação',
  'padaria': 'Alimentação',
  'açaí': 'Alimentação',
  'sorvete': 'Alimentação',
  'bar': 'Alimentação',
  'pet': 'Varejo',
  'petshop': 'Varejo',
  'pet shop': 'Varejo',
  'veterinária': 'Saúde',
  'veterinario': 'Saúde',
  'clínica': 'Saúde',
  'odontológica': 'Saúde',
  'dentista': 'Saúde',
  'estética': 'Saúde',
  'academia': 'Saúde',
  'fitness': 'Saúde',
  'crossfit': 'Saúde',
  'pilates': 'Saúde',
  'escola': 'Educação',
  'curso': 'Educação',
  'inglês': 'Educação',
  'idiomas': 'Educação',
  'informática': 'Tecnologia',
  'tecnologia': 'Tecnologia',
  'celular': 'Tecnologia',
  'eletrônicos': 'Tecnologia',
  'roupas': 'Varejo',
  'moda': 'Varejo',
  'boutique': 'Varejo',
  'calçados': 'Varejo',
  'sapatos': 'Varejo',
  'ótica': 'Varejo',
  'farmácia': 'Saúde',
  'drogaria': 'Saúde',
  'cosméticos': 'Varejo',
  'beleza': 'Serviços',
  'salão': 'Serviços',
  'barbearia': 'Serviços',
  'barbeiro': 'Serviços',
  'lavanderia': 'Serviços',
  'oficina': 'Serviços',
  'mecânica': 'Serviços',
  'contabilidade': 'Serviços',
  'advocacia': 'Serviços',
  'advogado': 'Serviços',
  'escritório': 'Serviços',
  'coworking': 'Serviços',
};

function identifyNiche(query: string): string {
  const lowerQuery = query.toLowerCase();
  for (const [keyword, niche] of Object.entries(productToNiche)) {
    if (lowerQuery.includes(keyword)) {
      return niche;
    }
  }
  return commercialTypes[Math.floor(Math.random() * commercialTypes.length)];
}

function generateRegions(product: string, niche: string): Region[] {
  const regions: Region[] = [];
  const usedNeighborhoods = new Set<number>();
  const numRegions = 40 + Math.floor(Math.random() * 10);

  for (let i = 0; i < numRegions; i++) {
    let neighborhoodIndex: number;
    do {
      neighborhoodIndex = Math.floor(Math.random() * fortalezaNeighborhoods.length);
    } while (usedNeighborhoods.has(neighborhoodIndex) && usedNeighborhoods.size < fortalezaNeighborhoods.length);
    
    if (usedNeighborhoods.size >= fortalezaNeighborhoods.length) {
      neighborhoodIndex = Math.floor(Math.random() * fortalezaNeighborhoods.length);
    }
    usedNeighborhoods.add(neighborhoodIndex);

    const neighborhood = fortalezaNeighborhoods[neighborhoodIndex];
    
    // Adiciona variação nas coordenadas para múltiplas regiões no mesmo bairro
    const latOffset = (Math.random() - 0.5) * 0.01;
    const lngOffset = (Math.random() - 0.5) * 0.01;

    // Score baseado em características do bairro (bairros nobres têm score maior)
    const nobleBairros = ['Aldeota', 'Meireles', 'Cocó', 'Dionísio Torres', 'Guararapes', 'Luciano Cavalcante'];
    const isNoble = nobleBairros.includes(neighborhood.name);
    const baseScore = isNoble ? 70 + Math.random() * 25 : 40 + Math.random() * 45;
    
    const region: Region = {
      id: `region-${i + 1}`,
      name: `${neighborhood.name} - Região ${i + 1}`,
      score: Math.round(baseScore * 10) / 10,
      potential: Math.round((baseScore * 0.9 + Math.random() * 10) * 10) / 10,
      lat: neighborhood.lat + latOffset,
      lng: neighborhood.lng + lngOffset,
      socialClass: isNoble 
        ? (Math.random() > 0.3 ? 'A' : 'B') 
        : socialClasses[Math.floor(Math.random() * 5)],
      commercialType: Math.random() > 0.6 ? niche : commercialTypes[Math.floor(Math.random() * commercialTypes.length)],
      pois: Math.floor(Math.random() * 50) + 5,
      population: Math.floor(Math.random() * 50000) + 10000,
      competitors: Math.floor(Math.random() * 15),
    };

    regions.push(region);
  }

  // Ordena por score decrescente
  return regions.sort((a, b) => b.score - a.score);
}

function generateInsights(product: string, niche: string, regions: Region[]): string[] {
  const topRegion = regions[0];
  const avgScore = regions.reduce((sum, r) => sum + r.score, 0) / regions.length;
  const classACount = regions.filter(r => r.socialClass === 'A').length;
  const classBCount = regions.filter(r => r.socialClass === 'B').length;

  return [
    `O nicho de ${niche} apresenta alta demanda na região de ${topRegion.name.split(' - ')[0]}, com score de ${topRegion.score.toFixed(1)} pontos.`,
    `${classACount + classBCount} regiões (${((classACount + classBCount) / regions.length * 100).toFixed(0)}%) estão em áreas com classes sociais A e B, indicando maior poder aquisitivo.`,
    `A média de score das regiões analisadas é ${avgScore.toFixed(1)}, acima da média do mercado (65 pontos).`,
    `Identificamos ${regions.filter(r => r.competitors < 5).length} regiões com baixa concorrência (menos de 5 competidores), representando oportunidades inexploradas.`,
    `O fluxo de pessoas nas regiões top 5 é 40% maior nos horários de pico (12h-14h e 18h-20h), ideal para ${product.toLowerCase()}.`,
  ];
}

function generateActionPlan(product: string, niche: string): ActionItem[] {
  return [
    { id: '1', text: `Visitar as 3 regiões com maior score para análise presencial`, checked: false },
    { id: '2', text: `Realizar pesquisa de mercado com potenciais clientes da região`, checked: false },
    { id: '3', text: `Verificar disponibilidade e preços de pontos comerciais`, checked: false },
    { id: '4', text: `Analisar concorrência direta nas regiões selecionadas`, checked: false },
    { id: '5', text: `Elaborar plano de negócios com projeções financeiras`, checked: false },
    { id: '6', text: `Consultar requisitos legais e licenças necessárias para ${niche.toLowerCase()}`, checked: false },
  ];
}

function generateStrategy(product: string, niche: string, regions: Region[]): Strategy {
  const topRegions = regions.slice(0, 5).map(r => r.name.split(' - ')[0]);
  const avgScore = regions.reduce((sum, r) => sum + r.score, 0) / regions.length;

  return {
    summary: `Análise completa para ${product} no segmento de ${niche} em Fortaleza. Identificamos ${regions.length} regiões potenciais com score médio de ${avgScore.toFixed(1)} pontos.`,
    executiveSummary: `Com base em nossa análise geoespacial e de mercado, recomendamos fortemente a expansão de ${product} nas regiões de ${topRegions.slice(0, 3).join(', ')}. Estas áreas apresentam a combinação ideal de: alto poder aquisitivo, baixa saturação de mercado e fluxo intenso de potenciais clientes. O investimento estimado para abertura varia entre R$ 80.000 e R$ 250.000, com payback projetado em 18-24 meses.`,
    targetAudience: `O público-alvo principal são moradores e trabalhadores das classes A e B, entre 25-55 anos, com renda familiar acima de R$ 8.000. Secundariamente, turistas e visitantes das regiões nobres de Fortaleza, especialmente nos bairros de Meireles e Aldeota.`,
    marketPotential: `O mercado de ${niche} em Fortaleza movimenta aproximadamente R$ 2,5 bilhões anuais, com crescimento de 12% ao ano. As regiões identificadas representam 35% deste mercado, com potencial de captura de 5-8% de market share nos primeiros 2 anos de operação.`,
    recommendations: [
      `Priorizar abertura em ${topRegions[0]} - maior score e menor concorrência`,
      `Implementar estratégia de marketing digital focada em geolocalização`,
      `Estabelecer parcerias com negócios complementares da região`,
      `Investir em experiência do cliente para gerar indicações`,
      `Considerar modelo de delivery/e-commerce como canal secundário`,
      `Monitorar continuamente métricas de mercado e ajustar estratégia`,
    ],
    nextSteps: [
      `Semana 1-2: Visitas técnicas às 5 regiões prioritárias`,
      `Semana 3-4: Pesquisa de mercado com 200+ potenciais clientes`,
      `Mês 2: Negociação de ponto comercial e elaboração de projeto`,
      `Mês 3-4: Obras, licenças e contratação de equipe`,
      `Mês 5: Soft opening e ajustes operacionais`,
      `Mês 6: Grand opening com campanha de marketing`,
    ],
  };
}

function generateDemographics(regions: Region[]): Demographics {
  const classCount: { [key: string]: number } = { A: 0, B: 0, C: 0, D: 0, E: 0 };
  const typeCount: { [key: string]: number } = {};

  regions.forEach(region => {
    classCount[region.socialClass]++;
    typeCount[region.commercialType] = (typeCount[region.commercialType] || 0) + 1;
  });

  const classColors: { [key: string]: string } = {
    A: 'hsl(142, 71%, 45%)',
    B: 'hsl(217, 91%, 60%)',
    C: 'hsl(45, 93%, 47%)',
    D: 'hsl(24, 94%, 50%)',
    E: 'hsl(0, 84%, 60%)',
  };

  const typeColors: { [key: string]: string } = {
    Varejo: 'hsl(142, 71%, 45%)',
    Serviços: 'hsl(217, 91%, 60%)',
    Alimentação: 'hsl(45, 93%, 47%)',
    Saúde: 'hsl(280, 87%, 65%)',
    Educação: 'hsl(24, 94%, 50%)',
    Tecnologia: 'hsl(180, 70%, 45%)',
  };

  return {
    socialClasses: Object.entries(classCount).map(([name, value]) => ({
      name: `Classe ${name}`,
      value,
      fill: classColors[name],
    })),
    commercialTypes: Object.entries(typeCount).map(([name, count]) => ({
      name,
      count,
      fill: typeColors[name] || 'hsl(215, 20%, 65%)',
    })),
  };
}

export function generateMockAnalysis(query: string): AnalysisResult {
  const product = query.split(/\s+em\s+|\s+para\s+|\s+na\s+|\s+no\s+/i)[0].trim() || query;
  const niche = identifyNiche(query);
  const regions = generateRegions(product, niche);
  const topRegion = regions[0];
  
  // Conta tipos comerciais
  const typeCount: { [key: string]: number } = {};
  regions.forEach(r => {
    typeCount[r.commercialType] = (typeCount[r.commercialType] || 0) + 1;
  });
  const topType = Object.entries(typeCount).sort((a, b) => b[1] - a[1])[0][0];

  return {
    product,
    niche,
    totalRegions: regions.length,
    avgScore: Math.round((regions.reduce((sum, r) => sum + r.score, 0) / regions.length) * 10) / 10,
    topNeighborhood: topRegion.name.split(' - ')[0],
    topCommercialType: topType,
    regions,
    insights: generateInsights(product, niche, regions),
    actionPlan: generateActionPlan(product, niche),
    strategy: generateStrategy(product, niche, regions),
    demographics: generateDemographics(regions),
  };
}

export const searchSuggestions = [
  'Cafeteria gourmet',
  'Pet shop',
  'Clínica odontológica',
  'Hamburgueria artesanal',
  'Loja de roupas femininas',
  'Academia de musculação',
  'Salão de beleza',
  'Restaurante japonês',
  'Escola de inglês',
  'Farmácia',
  'Barbearia moderna',
  'Pizzaria delivery',
  'Clínica de estética',
  'Loja de eletrônicos',
  'Padaria artesanal',
];

export const neighborhoodsList = fortalezaNeighborhoods.map(n => n.name);
