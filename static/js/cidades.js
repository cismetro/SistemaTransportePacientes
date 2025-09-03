// Script para gerenciar as cidades de São Paulo
class CidadesSP {
    constructor() {
        this.cidades = [];
        this.selectElement = null;
        this.inputElement = null;
        this.isLoaded = false;
    }

    // Carregar as cidades do JSON
    async loadCidades() {
        try {
            console.log('🏙️ Carregando cidades de São Paulo...');
            const response = await fetch('/static/data/cidades_sp.json');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.cidades = data.cidades.sort(); // Ordenar alfabeticamente
            this.isLoaded = true;
            
            console.log(`✅ ${this.cidades.length} cidades carregadas!`);
            return this.cidades;
        } catch (error) {
            console.error('❌ Erro ao carregar cidades:', error);
            // Fallback com algumas cidades principais
            this.cidades = [
                'São Paulo', 'Campinas', 'Santos', 'Ribeirão Preto', 
                'Sorocaba', 'Guarulhos', 'Osasco', 'Cosmópolis',
				'Adamantina', 'Adolfo', 'Aguaí', 'Águas da Prata', 'Águas de Lindóia',
				'Águas de Santa Bárbara', 'Águas de São Pedro', 'Agudos', 'Alambari', 'Alfredo Marcondes',
				'Altair', 'Altinópolis', 'Alto Alegre', 'Alumínio', 'Álvares Florence',
				'Álvares Machado', 'Álvaro de Carvalho', 'Alvinlândia', 'Americana', 'Américo Brasiliense',
				'Américo de Campos', 'Amparo', 'Analândia', 'Andradina', 'Angatuba',
				'Anhembi', 'Anhumas', 'Aparecida', 'Aparecida d\'Oeste', 'Apiaí',
				'Araçariguama', 'Araçatuba', 'Araçoiaba da Serra', 'Aramina', 'Arandu',
				'Arapeí', 'Araraquara', 'Araras', 'Arco-Íris', 'Arealva',
				'Areias', 'Areiópolis', 'Ariranha', 'Artur Nogueira', 'Arujá',
				'Aspásia', 'Assis', 'Atibaia', 'Auriflama', 'Avaí',
				'Avanhandava', 'Avaré', 'Bady Bassitt', 'Balbinos', 'Bálsamo',
				'Bananal', 'Barão de Antonina', 'Barbosa', 'Bariri', 'Barra Bonita',
				'Barra do Chapéu', 'Barra do Turvo', 'Barretos', 'Barrinha', 'Barueri',
				'Bastos', 'Batatais', 'Bauru', 'Bebedouro', 'Bento de Abreu',
				'Bernardino de Campos', 'Bertioga', 'Bilac', 'Birigui', 'Biritiba-Mirim',
				'Boa Esperança do Sul', 'Bocaina', 'Bofete', 'Boituva', 'Bom Jesus dos Perdões',
				'Bom Sucesso de Itararé', 'Borá', 'Boracéia', 'Borborema', 'Borebi',
				'Botucatu', 'Bragança Paulista', 'Braúna', 'Brejo Alegre', 'Brodowski',
				'Brotas', 'Buri', 'Buritama', 'Buritizal', 'Cabrália Paulista',
				'Cabreúva', 'Caçapava', 'Cachoeira Paulista', 'Caconde', 'Cafelândia',
				'Caiabu', 'Caieiras', 'Caiuá', 'Cajamar', 'Cajati',
				'Cajobi', 'Cajuru', 'Campina do Monte Alegre', 'Campinas', 'Campo Limpo Paulista',
				'Campos do Jordão', 'Campos Novos Paulista', 'Cananéia', 'Canas', 'Cândido Mota',
				'Cândido Rodrigues', 'Canitar', 'Capão Bonito', 'Capela do Alto', 'Capivari',
				'Caraguatatuba', 'Carapicuíba', 'Cardoso', 'Casa Branca', 'Cássia dos Coqueiros',
				'Castilho', 'Catanduva', 'Catiguá', 'Cedral', 'Cerqueira César',
				'Cerquilho', 'Cesário Lange', 'Charqueada', 'Chavantes', 'Clementina',
				'Colina', 'Colômbia', 'Conchal', 'Conchas', 'Cordeirópolis',
				'Coroados', 'Coronel Macedo', 'Corumbataí', 'Cosmópolis', 'Cosmorama',
				'Cotia', 'Cravinhos', 'Cristais Paulista', 'Cruzália', 'Cruzeiro',
				'Cubatão', 'Cunha', 'Descalvado', 'Diadema', 'Dirce Reis',
				'Divinolândia', 'Dobrada', 'Dois Córregos', 'Dolcinópolis', 'Dourado',
				'Dracena', 'Duartina', 'Dumont', 'Echaporã', 'Eldorado',
				'Elias Fausto', 'Elisiário', 'Embaúba', 'Embu das Artes', 'Embu-Guaçu',
				'Emilianópolis', 'Engenheiro Coelho', 'Espírito Santo do Pinhal', 'Espírito Santo do Turvo', 'Estiva Gerbi','Estrela d\'Oeste', 'Estrela do Norte', 'Euclides da Cunha Paulista', 'Fartura', 'Fernando Prestes','Fernandópolis', 'Fernão', 'Ferraz de Vasconcelos', 'Flora Rica', 'Floreal',			'Flórida Paulista', 'Florínea', 'Franca', 'Francisco Morato', 'Franco da Rocha',
				'Gabriel Monteiro', 'Gália', 'Garça', 'Gastão Vidigal', 'Gavião Peixoto',
				'General Salgado', 'Getulina', 'Glicério', 'Guaiçara', 'Guaimbê',
				'Guaíra', 'Guapiaçu', 'Guapiara', 'Guará', 'Guaraçaí',
				'Guaraci', 'Guarani d\'Oeste', 'Guarantã', 'Guararapes', 'Guararema',
				'Guaratinguetá', 'Guareí', 'Guariba', 'Guarujá', 'Guarulhos',
				'Guatapará', 'Guzolândia', 'Herculândia', 'Holambra', 'Hortolândia',
				'Iacanga', 'Iacri', 'Iaras', 'Ibaté', 'Ibirá',
				'Ibirarema', 'Ibitinga', 'Ibiúna', 'Icém', 'Iepê',
				'Igaraçu do Tietê', 'Igarapava', 'Igaratá', 'Iguape', 'Ilhabela',
				'Ilha Comprida', 'Ilha Solteira', 'Indaiatuba', 'Indiana', 'Indiaporã',
				'Inúbia Paulista', 'Ipaussu', 'Iperó', 'Ipeúna', 'Ipiguá',
				'Iporanga', 'Ipuã', 'Iracemápolis', 'Irapuã', 'Irapuru',
				'Itaberá', 'Itai', 'Itajobi', 'Itaju', 'Itanhaém',
				'Itaóca', 'Itapecerica da Serra', 'Itapetininga', 'Itapeva', 'Itapevi',
				'Itapira', 'Itapirapuã Paulista', 'Itápolis', 'Itaporanga', 'Itapuí',
				'Itapura', 'Itaquaquecetuba', 'Itararé', 'Itariri', 'Itatiba',
				'Itatinga', 'Itirapina', 'Itirapuã', 'Itobi', 'Itu',
				'Itupeva', 'Ituverava', 'Jaborandi', 'Jaboticabal', 'Jacareí',
				'Jaci', 'Jacupiranga', 'Jaguariúna', 'Jales', 'Jambeiro',
				'Jandira', 'Jardinópolis', 'Jarinu', 'Jaú', 'Jeriquara',
				'Joanópolis', 'João Ramalho', 'José Bonifácio', 'Júlio Mesquita', 'Jumirim',
				'Jundiaí', 'Junqueirópolis', 'Juquiá', 'Juquitiba', 'Lagoinha',
				'Laranjal Paulista', 'Lavínia', 'Lavrinhas', 'Leme', 'Lençóis Paulista',
				'Limeira', 'Lindóia', 'Lins', 'Lorena', 'Lourdes',
				'Louveira', 'Lucélia', 'Lucianópolis', 'Luís Antônio', 'Luiziânia',
				'Lupércio', 'Lutécia', 'Macatuba', 'Macaubal', 'Macedônia',
				'Magda', 'Mairinque', 'Mairiporã', 'Manduri', 'Marabá Paulista',
				'Maracaí', 'Marapoama', 'Mariápolis', 'Marília', 'Marinópolis',
				'Martinópolis', 'Matão', 'Mauá', 'Mendonça', 'Meridiano','Mesópolis', 'Miguelópolis', 'Mineiros do Tietê', 'Mira Estrela', 'Miracatu',
			'Mirandópolis', 'Mirante do Paranapanema', 'Mirassol', 'Mirassolândia', 'Mococa',
			'Mogi das Cruzes', 'Mogi Guaçu', 'Moji Mirim', 'Mombuca', 'Monções',
			'Mongaguá', 'Monte Alegre do Sul', 'Monte Alto', 'Monte Aprazível', 'Monte Azul Paulista','Monte Castelo','Monte Mor', 'Monteiro Lobato', 'Morro Agudo', 'Morungaba','Motuca', 'Murutinga do Sul', 'Nantes', 'Narandiba', 'Natividade da Serra','Nazaré Paulista', 'Neves Paulista', 'Nhandeara', 'Nipoã', 'Nova Aliança','Nova Campina', 'Nova Canaã Paulista', 'Nova Castilho', 'Nova Europa', 'Nova Granada','Nova Guataporanga','Nova Independência', 'Nova Luzitânia', 'Nova Odessa', 'Novais',
			'Novo Horizonte', 'Nuporanga', 'Ocauçu', 'Óleo', 'Olímpia',
			'Onda Verde', 'Oriente', 'Orindiúva', 'Orlândia', 'Osasco',
			'Oscar Bressane', 'Osvaldo Cruz', 'Ourinhos', 'Ouro Verde', 'Ouroeste',
			'Pacaembu', 'Palestina', 'Palmares Paulista', 'Palmeira d\'Oeste', 'Palmital',
			'Panorama', 'Paraguaçu Paulista', 'Paraibuna', 'Paraíso', 'Paranapanema',
			'Paranapuã', 'Parapuã', 'Pardinho', 'Pariquera-Açu', 'Parisi',
			'Patrocínio Paulista', 'Paulicéia', 'Paulínia', 'Paulistânia', 'Paulo de Faria',
			'Pederneiras', 'Pedra Bela', 'Pedranópolis', 'Pedregulho', 'Pedreira',
			'Pedrinhas Paulista', 'Pedro de Toledo', 'Penápolis', 'Pereira Barreto', 'Pereiras',
			'Peruíbe', 'Piedade', 'Pilar do Sul', 'Pindamonhangaba', 'Pindorama', 
			'Pinhalzinho', 'Piquerobi', 'Piquete', 'Piracaia', 'Piracicaba', 
			'Piraju', 'Pirajuí', 'Pirangi', 'Pirapora do Bom Jesus', 'Pirapozinho', 
			'Pirassununga', 'Piratininga', 'Pitangueiras', 'Planalto', 'Platina', 
			'Poá', 'Poloni', 'Pompéia', 'Pongaí', 'Pontal', 'Pontalinda', 
			'Pontes Gestal', 'Populina', 'Porangaba', 'Porto Feliz', 'Porto Ferreira', 
			'Potim', 'Potirendaba', 'Pracinha', 'Pradópolis', 'Praia Grande', 
			'Pratânia', 'Presidente Alves', 'Presidente Bernardes', 'Presidente Epitácio', 
			'Presidente Prudente', 'Presidente Venceslau', 'Promissão', 'Quadra', 
			'Quatá', 'Queiroz', 'Queluz', 'Quintana', 'Rafard', 'Rancharia', 
			'Redenção da Serra', 'Regente Feijó', 'Reginópolis', 'Registro', 
			'Restinga', 'Ribeira', 'Ribeirão Bonito', 'Ribeirão Branco', 'Ribeirão Corrente', 
			'Ribeirão do Sul', 'Ribeirão dos Índios', 'Ribeirão Grande', 'Ribeirão Pires', 
			'Ribeirão Preto', 'Rifaina', 'Rincão', 'Rinópolis', 'Rio Claro', 
			'Rio das Pedras', 'Rio Grande da Serra', 'Riolândia', 'Riversul', 'Rosana', 
			'Roseira', 'Rubiácea', 'Rubinéia', 'Sabino', 'Sagres', 'Sales', 
			'Sales Oliveira', 'Salesópolis', 'Salmourão', 'Saltinho', 'Salto', 
			'Salto de Pirapora', 'Salto Grande', 'Sandovalina', 'Santa Adélia', 
			'Santa Albertina', 'Santa Bárbara d\'Oeste', 'Santa Branca', 'Santa Clara d\'Oeste', 
			'Santa Cruz da Conceição', 'Santa Cruz da Esperança', 'Santa Cruz das Palmeiras', 
			'Santa Cruz do Rio Pardo', 'Santa Ernestina', 'Santa Fé do Sul', 
			'Santa Gertrudes', 'Santa Isabel', 'Santa Lúcia', 'Santa Maria da Serra', 
			'Santa Mercedes', 'Santa Rita d\'Oeste', 'Santa Rita do Passa Quatro', 
			'Santa Rosa de Viterbo', 'Santa Salete', 'Santana da Ponte Pensa', 
			'Santana de Parnaíba', 'Santo Anastácio', 'Santo André', 'Santo Antônio da Alegria', 
			'Santo Antônio de Posse', 'Santo Antônio do Aracanguá', 'Santo Antônio do Jardim', 
			'Santo Antônio do Pinhal', 'Santo Expedito', 'Santópolis do Aguapeí', 
			'Santos', 'São Bento do Sapucaí', 'São Bernardo do Campo', 'São Caetano do Sul', 
			'São Carlos', 'São Francisco', 'São João da Boa Vista', 'São João das Duas Pontes',
			'São João de Iracema','São João do Pau dalho','São Joaquim da Barra','São José da Bela Vista','São José do Barreiro','São José do Rio Pardo','São José do Rio Preto','São José dos Campos',
			'São Lourenço da Serra','São Luiz do Paraitinga','São Manuel','São Miguel','Arcanjo','São Paulo',
			'São Pedro','São Pedro do Turvo','São Roque','São Sebastião','São Sebastião da Grama','São Simão','São Vicente','Sarapuí',
			'Sarutaiá','Sebastianópolis do Sul','Serra Azul','Serra Negra','Serrana','Sertãozinho','Sete  Barras','Severínia','Silveiras',
			'Socorro','Sorocaba','Sud Mennucci','Sumaré','Suzanápolis','Suzano','Tabapuã','Tabatinga','Taboão da Serra','Taciba','Taguaí','Taiaçu','Taiúva',			'Tambaú','Tanabi','Tapiraí','Tapiratiba','Taquaral','Taquaritinga','Taquarituba','Taquarivaí',
			'Tarabai','Tarumã','Tatuí','Taubaté','Tejupá','Teodoro Sampaio','Terra Roxa','Tietê','Timburi',
			'Torre de Pedra','Torrinha','Trabiju','Tremembé','Três Fronteiras','Tuiuti','Tupã','Tupi Paulista',
			'Turiúba','Turmalina','Ubarana','Ubatuba','Ubirajara','Uchoa','União Paulista','Urânia', 'Uru',
			'Urupês','Valentim Gentil','Valinhos','Valparaíso','Vargem','Vargem Grande do Sul','Vargem Grande Paulista',
			'Várzea Paulista','Vera Cruz','Vinhedo','Viradouro','Vista Alegre do Alto','Vitória Brasil','Votorantim','Votuporanga','Zacarias','Peruíbe'
            ];
            this.isLoaded = true;
            return this.cidades;
        }
    }

    // Criar o select de cidades
    createCidadeSelect(targetElementId, placeholder = 'Selecione a cidade...') {
        const container = document.getElementById(targetElementId);
        if (!container) {
            console.error(`❌ Elemento ${targetElementId} não encontrado!`);
            return;
        }

        // Criar o select
        const select = document.createElement('select');
        select.id = `${targetElementId}_select`;
        select.className = 'form-control cidade-select';
        select.style.marginBottom = '0.5rem';

        // Opção padrão
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = placeholder;
        select.appendChild(defaultOption);

        // Adicionar as cidades
        this.cidades.forEach(cidade => {
            const option = document.createElement('option');
            option.value = cidade;
            option.textContent = cidade;
            select.appendChild(option);
        });

        // Opção "Outra cidade"
        const outraOption = document.createElement('option');
        outraOption.value = 'outra';
        outraOption.textContent = '🏙️ Outra cidade (digite abaixo)';
        select.appendChild(outraOption);

        // Inserir o select antes do input existente
        const inputElement = container.querySelector('input');
        if (inputElement) {
            this.inputElement = inputElement;
            this.inputElement.placeholder = 'Digite o endereço completo ou selecione uma cidade acima';
            container.insertBefore(select, inputElement);
            
            // Event listener para o select
            select.addEventListener('change', (e) => {
                const selectedValue = e.target.value;
                if (selectedValue && selectedValue !== 'outra') {
                    // Preencher o input com a cidade selecionada
                    this.inputElement.value = selectedValue + ', SP';
                    this.inputElement.focus();
                    // Posicionar cursor no final
                    setTimeout(() => {
                        this.inputElement.setSelectionRange(this.inputElement.value.length, this.inputElement.value.length);
                    }, 100);
                } else if (selectedValue === 'outra') {
                    // Limpar e focar no input para digitação livre
                    this.inputElement.value = '';
                    this.inputElement.focus();
                    this.inputElement.placeholder = 'Digite o endereço completo da cidade';
                }
            });

            this.selectElement = select;
            console.log('✅ Select de cidades criado com sucesso!');
        } else {
            console.error('❌ Input não encontrado no container!');
        }
    }

    // Inicializar o sistema
    async init(targetElementId, placeholder) {
        await this.loadCidades();
        this.createCidadeSelect(targetElementId, placeholder);
    }

    // Método para buscar cidade por nome (para autocomplete futuro)
    searchCidade(query) {
        if (!query || query.length < 2) return [];
        
        const queryLower = query.toLowerCase();
        return this.cidades.filter(cidade => 
            cidade.toLowerCase().includes(queryLower)
        );
    }

    // Validar se a cidade existe
    isValidCidade(cidade) {
        return this.cidades.includes(cidade);
    }
}

// Instância global
const cidadesSP = new CidadesSP();

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Iniciando sistema de cidades...');
    
    // Verificar se estamos na página de agendamento
    const targetElement = document.getElementById('destino');
    if (targetElement) {
        // Aguardar um pouco para garantir que tudo foi carregado
        setTimeout(() => {
            cidadesSP.init('destino-container', '🏙️ Selecione a cidade de destino...');
        }, 500);
    }
});

// Função para validar formulário (opcional)
function validateDestinoForm() {
    const destinoInput = document.getElementById('destino');
    if (destinoInput && destinoInput.value.trim() === '') {
        alert('Por favor, selecione uma cidade ou digite o endereço de destino!');
        return false;
    }
    return true;
}

// =======VALIDAÇÃO PARA O PREENCHIMENTO DO  FORMULÁRIO ========

// Função de validação simples para destino
function validarDestinoSimples() {
    const destinoInput = document.getElementById('destino');
    if (!destinoInput) return true;
    
    const valor = destinoInput.value.trim();
    
    // Se estiver vazio, não validar ainda
    if (!valor) return true;
    
    // Se tem menos de 5 caracteres, muito curto
    if (valor.length < 5) return true;
    
    // Palavras que indicam endereço válido
    const palavrasValidas = [
        'rua', 'av', 'avenida', 'alameda', 'travessa', 'praça', 'praca',
        'estrada', 'rodovia', 'br', 'sp', 'centro', 'bairro', 'jardim', 
        'vila', 'conjunto', 'hospital', 'clinica', 'clínica', 'posto', 
        'ubs', 'santa casa', 'hospital', 'número', 'nº', 'n°', 'km'
    ];
    
    const valorLower = valor.toLowerCase();
    
    // Verificar se tem pelo menos uma palavra válida
    const temPalavraValida = palavrasValidas.some(palavra => 
        valorLower.includes(palavra)
    );
    
    // Verificar se tem números (indica endereço)
    const temNumeros = /\d/.test(valor);
    
    // Se tem palavra válida OU números, é válido
    if (temPalavraValida || temNumeros) {
        mostrarSucessoDestino();
        return true;
    } else {
        mostrarAvisoDestino();
        return false;
    }
}

// Mostrar aviso simples
function mostrarAvisoDestino() {
    const input = document.getElementById('destino');
    if (!input) return;
    
    // Remover aviso anterior
    const avisoAnterior = input.parentElement.querySelector('.aviso-destino');
    if (avisoAnterior) avisoAnterior.remove();
    
    // Criar novo aviso
    const aviso = document.createElement('div');
    aviso.className = 'aviso-destino';
    aviso.style.cssText = `
        color: #f2823c;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        display: flex;
        align-items: center;
    `;
    aviso.innerHTML = `
        <span style="margin-right: 0.5rem;">💡</span>
        <span>Digite um endereço completo (ex: Rua das Flores, 123, Centro)</span>
    `;
    
    input.parentElement.appendChild(aviso);
    
    // Bordar laranja
    input.style.borderColor = '#f2823c';
}

// Mostrar sucesso
function mostrarSucessoDestino() {
    const input = document.getElementById('destino');
    if (!input) return;
    
    // Remover avisos
    const avisoAnterior = input.parentElement.querySelector('.aviso-destino');
    if (avisoAnterior) avisoAnterior.remove();
    
    // Bordar verde
    input.style.borderColor = '#79b24a';
    
    // Remover cor após 2 segundos
    setTimeout(() => {
        input.style.borderColor = 'var(--border-color, #e5e5e5)';
    }, 2000);
}

// Adicionar validação ao input quando sair do campo
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        const destinoInput = document.getElementById('destino');
        if (destinoInput) {
            destinoInput.addEventListener('blur', validarDestinoSimples);
            
            // Também validar enquanto digita (com delay)
            let timeoutId;
            destinoInput.addEventListener('input', function() {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    if (this.value.length > 10) {
                        validarDestinoSimples();
                    }
                }, 1000);
            });
        }
    }, 1000);
});