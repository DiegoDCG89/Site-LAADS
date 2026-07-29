# 🦆 LaADS — Site Institucional

<div align="center">

<img src="https://img.shields.io/badge/LaADS-Liga%20Acadêmica%20de%20ADS-2563EB?style=for-the-badge" alt="LaADS">

<br><br>

**Da teoria para a prática.**

Site institucional desenvolvido para a **Liga Acadêmica de Análise e Desenvolvimento de Sistemas (LaADS)**, com foco em apresentar a organização, divulgar suas atividades e centralizar informações sobre eventos, projetos e iniciativas acadêmicas.

<br>

[🌐 Site](#-demonstração) •
[📖 Sobre](#-sobre-o-projeto) •
[✨ Funcionalidades](#-funcionalidades) •
[🛠️ Tecnologias](#️-tecnologias) •
[🔐 Segurança](#-segurança) •
[🚀 Instalação](#-instalação) •
[🗺️ Roadmap](#️-roadmap)

</div>

---

## 📌 Sobre o Projeto

O **LaADS — Site Institucional** é uma aplicação web criada para fortalecer a presença digital da **Liga Acadêmica de Análise e Desenvolvimento de Sistemas**, proporcionando um espaço centralizado para divulgação da liga e de suas atividades.

O projeto foi desenvolvido com uma abordagem moderna e responsiva, buscando proporcionar uma experiência simples e intuitiva para estudantes, professores, parceiros e visitantes.

A aplicação é dividida em duas áreas principais:

* **Área pública:** destinada à apresentação e divulgação das informações da LaADS;
* **Painel administrativo:** destinado ao gerenciamento do conteúdo da aplicação.

A proposta do projeto é aproximar a comunidade acadêmica da prática profissional, utilizando o desenvolvimento de software como ferramenta de aprendizado, colaboração e construção de projetos reais.

> **Onde estudantes de ADS saem da teoria e entram em produção: projetos reais, mentoria entre pares e uma comunidade que constrói software — e carreira — junto.**

---

## 🎯 Objetivos

O desenvolvimento do site tem como objetivos:

* Criar uma identidade digital para a LaADS;
* Apresentar a missão, visão e valores da liga;
* Divulgar eventos, palestras e workshops;
* Apresentar projetos e iniciativas desenvolvidas;
* Facilitar o acesso às informações da organização;
* Fortalecer a comunicação com estudantes e comunidade acadêmica;
* Centralizar informações institucionais em um único ambiente;
* Disponibilizar uma área administrativa para gerenciamento do conteúdo.

---

## ✨ Funcionalidades

### 🌐 Área Pública

A página institucional permite aos visitantes:

* Conhecer a LaADS;
* Conhecer a proposta e os objetivos da liga;
* Visualizar informações institucionais;
* Conhecer a missão, visão e valores;
* Acompanhar eventos e atividades;
* Conhecer projetos e iniciativas;
* Acessar informações de contato;
* Navegar por uma interface responsiva;
* Acessar o conteúdo por dispositivos desktop e mobile.

---

### 🔐 Painel Administrativo

O projeto possui uma área administrativa destinada ao gerenciamento das informações apresentadas no site.

O painel conta com:

* Tela de autenticação;
* Validação de credenciais;
* Controle de acesso ao painel;
* Gerenciamento de conteúdo;
* Gerenciamento de informações institucionais;
* Gerenciamento de eventos;
* Gerenciamento de imagens;
* Interface administrativa dedicada.

A separação entre a área pública e o painel administrativo permite que o conteúdo institucional seja gerenciado de forma centralizada.

---

### 🛡️ Recursos de Segurança

O projeto utiliza recursos de segurança para proteger o acesso à área administrativa, incluindo:

* Autenticação por credenciais;
* Hash criptográfico de senha;
* Validação de acesso;
* Restrição de acesso ao painel administrativo;
* Página dedicada a informações de privacidade.

> **Importante:** a implementação atual utiliza SHA-256 para hashing. Para um ambiente de produção com requisitos de segurança mais elevados, recomenda-se migrar a autenticação para um backend com armazenamento seguro de senhas utilizando algoritmos específicos para password hashing, como **Argon2id** ou **bcrypt**.

---

## 🖥️ Demonstração

A aplicação é composta por uma interface institucional pública e uma área administrativa.

### Página Institucional

A página pública apresenta a identidade da LaADS e seus principais conteúdos institucionais.

**Principais seções:**

* Apresentação;
* Sobre a liga;
* Missão, visão e valores;
* Projetos;
* Eventos;
* Informações de contato.

### Painel Administrativo

Área restrita responsável pelo gerenciamento do conteúdo da aplicação.

> 📸 **Sugestão:** adicione aqui uma captura de tela do painel administrativo e outra da página inicial. Isso melhora significativamente a apresentação do projeto no GitHub.

Exemplo:

```markdown
## 📸 Screenshots

### Página Inicial

![Página Inicial](./docs/screenshots/home.png)

### Painel Administrativo

![Painel Administrativo](./docs/screenshots/admin.png)
```

---

## 🏗️ Arquitetura da Aplicação

A aplicação segue uma arquitetura simples baseada em tecnologias web tradicionais.

```text
┌─────────────────────────────────────┐
│             USUÁRIO                 │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│          SITE INSTITUCIONAL         │
│             index.html              │
└──────────────────┬──────────────────┘
                   │
                   │ Conteúdo público
                   │
                   ▼
┌─────────────────────────────────────┐
│       PAINEL ADMINISTRATIVO         │
│             admin.html              │
└──────────────────┬──────────────────┘
                   │
                   │ Autenticação
                   ▼
┌─────────────────────────────────────┐
│       VALIDAÇÃO DE CREDENCIAIS      │
│           SHA-256 / Hash            │
└─────────────────────────────────────┘
```

A estrutura atual prioriza simplicidade e facilidade de manutenção, sendo adequada para um projeto institucional de pequeno porte.

---

## 🛠️ Tecnologias

O projeto foi desenvolvido utilizando tecnologias web amplamente utilizadas no mercado.

| Tecnologia         | Aplicação                             |
| ------------------ | ------------------------------------- |
| **HTML5**          | Estrutura e semântica das páginas     |
| **CSS3**           | Estilização e personalização visual   |
| **JavaScript**     | Lógica e interatividade               |
| **Tailwind CSS**   | Desenvolvimento da interface visual   |
| **Web Crypto API** | Operações criptográficas no navegador |
| **SHA-256**        | Hash utilizado na autenticação        |
| **Git**            | Controle de versão                    |
| **GitHub**         | Hospedagem e versionamento do projeto |

---

## 📂 Estrutura do Projeto

A estrutura principal da aplicação está organizada da seguinte maneira:

```text
LaADS/
│
├── index.html
│       └── Página institucional pública
│
├── admin.html
│       └── Painel administrativo
│
├── privacy.html
│       └── Política e informações de privacidade
│
├── diagnostic.html
│       └── Página de diagnóstico da aplicação
│
├── css/
│       └── Arquivos de estilos personalizados
│
├── js/
│       └── Scripts e lógica da aplicação
│
├── images/
│       └── Imagens utilizadas no projeto
│
├── uploads/
│       └── Arquivos e imagens gerenciados pela aplicação
│
└── README.md
        └── Documentação do projeto
```

> A estrutura acima deve ser ajustada caso os diretórios do repositório tenham nomes diferentes.

---

## 🚀 Instalação

### Pré-requisitos

Para executar o projeto localmente, você precisa ter:

* Git;
* Um navegador moderno;
* Visual Studio Code ou outro editor de código;
* Extensão **Live Server** ou um servidor HTTP local.

---

### 1. Clone o repositório

```bash
git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
```

---

### 2. Acesse o diretório

```bash
cd SEU-REPOSITORIO
```

---

### 3. Execute o projeto

Abra o arquivo:

```text
index.html
```

Você também pode utilizar o **Live Server** para executar a aplicação.

Alternativamente, caso tenha Python instalado:

```bash
python -m http.server 8000
```

Acesse:

```text
http://localhost:8000
```

---

## 🔑 Acesso ao Painel Administrativo

O painel administrativo está disponível através do arquivo:

```text
admin.html
```

O acesso é protegido por autenticação.

> **Não coloque credenciais reais, senhas ou hashes sensíveis diretamente no README ou no repositório público.**

Em um ambiente de produção, recomenda-se utilizar um sistema de autenticação baseado em servidor e variáveis de ambiente.

---

## 🔒 Considerações de Segurança

A aplicação atual foi desenvolvida com foco em um projeto institucional e acadêmico. Para uma utilização em produção, algumas melhorias podem ser consideradas.

### Implementações recomendadas

* [ ] Migrar autenticação para um backend;
* [ ] Utilizar HTTPS obrigatoriamente;
* [ ] Utilizar Argon2id ou bcrypt para armazenamento de senhas;
* [ ] Implementar sessões seguras;
* [ ] Adicionar expiração de sessão;
* [ ] Implementar controle de permissões;
* [ ] Validar dados também no servidor;
* [ ] Implementar proteção contra XSS;
* [ ] Implementar proteção contra CSRF quando aplicável;
* [ ] Utilizar variáveis de ambiente;
* [ ] Implementar logs de acesso;
* [ ] Adicionar política de backup;
* [ ] Configurar headers de segurança HTTP.

### ⚠️ Importante

O uso de SHA-256 diretamente para armazenar senhas **não é recomendado para sistemas de autenticação em produção**, pois algoritmos rápidos de hash são vulneráveis a ataques de força bruta e dicionário quando utilizados sem mecanismos específicos para password hashing.

Para aplicações reais, prefira:

```text
Senha do usuário
       │
       ▼
Argon2id / bcrypt
       │
       ▼
Hash seguro
       │
       ▼
Banco de dados
```

---

## 🌍 Deploy

O projeto pode ser publicado em diferentes ambientes, dependendo da arquitetura utilizada.

Para a parte estática da aplicação, algumas alternativas incluem:

* GitHub Pages;
* Netlify;
* Vercel;
* Apache;
* Nginx;
* Serviços tradicionais de hospedagem web.

Caso o painel administrativo dependa de funcionalidades que exigem processamento no servidor, será necessário utilizar uma infraestrutura compatível com o backend responsável pela autenticação e gerenciamento dos dados.

---

## 🗺️ Roadmap

Possíveis evoluções futuras do projeto:

### Conteúdo

* [ ] Sistema completo de gerenciamento de eventos;
* [ ] Cadastro e edição de projetos;
* [ ] Gerenciamento de membros;
* [ ] Galeria de imagens;
* [ ] Sistema de notícias;
* [ ] Agenda de eventos.

### Administração

* [ ] Dashboard com métricas;
* [ ] Diferentes níveis de acesso;
* [ ] Gerenciamento de usuários administradores;
* [ ] Histórico de alterações;
* [ ] Sistema de logs.

### Segurança

* [ ] Backend para autenticação;
* [ ] Hashing com Argon2id ou bcrypt;
* [ ] Sessões seguras;
* [ ] HTTPS;
* [ ] Proteção contra ataques comuns;
* [ ] Variáveis de ambiente.

### Experiência

* [ ] Melhorias contínuas de acessibilidade;
* [ ] Otimização de performance;
* [ ] SEO;
* [ ] PWA;
* [ ] Melhorias na experiência mobile.

---

## 🤝 Contribuição

Contribuições são bem-vindas!

Para contribuir com o projeto:

### 1. Faça um Fork

Crie uma cópia do projeto para sua conta do GitHub.

### 2. Clone o repositório

```bash
git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
```

### 3. Crie uma branch

```bash
git checkout -b feature/minha-feature
```

### 4. Faça suas alterações

Implemente sua melhoria ou correção.

### 5. Faça o commit

```bash
git add .
git commit -m "feat: adiciona nova funcionalidade"
```

### 6. Envie para o GitHub

```bash
git push origin feature/minha-feature
```

### 7. Abra um Pull Request

Descreva as alterações realizadas e aguarde a revisão.

---

## 📋 Convenção de Commits

Recomenda-se utilizar mensagens de commit padronizadas:

```text
feat: nova funcionalidade
fix: correção de bug
docs: atualização da documentação
style: alterações de estilo
refactor: refatoração de código
perf: melhoria de performance
security: correção relacionada à segurança
```

Exemplos:

```bash
git commit -m "feat: adiciona gerenciamento de eventos"
```

```bash
git commit -m "fix: corrige autenticação do painel"
```

```bash
git commit -m "docs: atualiza README"
```

---

## 📄 Licença

Este projeto pertence à **Liga Acadêmica de Análise e Desenvolvimento de Sistemas (LaADS)**.

A definição da licença de uso, modificação e distribuição deve ser especificada no arquivo:

```text
LICENSE
```

Caso o projeto seja disponibilizado publicamente como código aberto, recomenda-se escolher uma licença compatível com os objetivos da LaADS.

---

## 🦆 Sobre a LaADS

A **Liga Acadêmica de Análise e Desenvolvimento de Sistemas (LaADS)** é uma iniciativa voltada ao desenvolvimento técnico e profissional de estudantes, buscando aproximar a formação acadêmica da realidade do mercado de tecnologia.

Por meio de projetos, eventos, palestras, workshops e atividades colaborativas, a liga busca criar um ambiente onde estudantes possam desenvolver suas habilidades e transformar conhecimento em prática.

### Nossa missão

> Aproximar teoria e prática, formando desenvolvedores prontos para o mercado desde o início da graduação.

### Nossa visão

> Ser referência entre ligas acadêmicas de tecnologia da região, promovendo inovação, colaboração e desenvolvimento profissional.

---

## 🚀 Da teoria para a prática

O site institucional da LaADS representa mais do que uma aplicação web.

Ele é parte de uma iniciativa construída por estudantes que buscam aprender, experimentar tecnologias, resolver problemas reais e desenvolver soluções que possam gerar impacto dentro e fora da universidade.

**Aprender. Construir. Compartilhar. Evoluir.**

### 🦆 LaADS

**Vamos construir o futuro juntos.**

---

<div align="center">

Desenvolvido com 💙 pela comunidade **LaADS**

**Liga Acadêmica de Análise e Desenvolvimento de Sistemas**

</div>
