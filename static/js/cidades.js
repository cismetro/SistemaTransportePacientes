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
                'Sorocaba', 'Guarulhos', 'Osasco', 'Cosmópolis'
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