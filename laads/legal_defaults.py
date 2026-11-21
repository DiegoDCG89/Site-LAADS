"""Textos-base das páginas /privacidade e /termos (editáveis em Painel > Páginas legais).

Formatação aceita: `## Título`, listas com `- item`, **negrito**, [texto](link) e parágrafos separados
por linha em branco. Os marcadores {entidade} e {email} são trocados pelos valores cadastrados no painel.

ATENÇÃO: é um modelo genérico, não substitui revisão jurídica da sua instituição.
"""

PRIVACY_DEFAULT = """\
## 1. Quem somos

Esta Política de Privacidade explica como {entidade} ("LaADS", "nós") trata os dados pessoais de quem visita este site e usa seus formulários, em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018, a LGPD). Para qualquer assunto sobre seus dados, fale com a gente em [{email}](mailto:{email}).

## 2. Quais dados coletamos

- **Formulário de inscrição:** nome, período, telefone, e-mail, squad de interesse e mensagem opcional.
- **Formulário de contato:** nome, e-mail e mensagem.
- **Dados técnicos de acesso:** endereço IP, tipo de navegador e data/hora do acesso, registrados automaticamente pela hospedagem por segurança e funcionamento do site.

Não pedimos dados pessoais sensíveis (como saúde, religião ou opinião política). Por favor, não os escreva nos campos de mensagem.

## 3. Para que usamos seus dados

- Analisar sua inscrição e entrar em contato sobre a participação na liga.
- Organizar squads, eventos e atividades.
- Responder dúvidas e mensagens enviadas pelo formulário de contato.
- Enviar comunicados diretamente relacionados à liga e aos seus eventos.
- Proteger o site contra spam, abusos e acessos indevidos.
- Cumprir obrigações legais, quando aplicável.

## 4. Bases legais

Tratamos seus dados com base no seu **consentimento** (ao enviar um formulário), na realização de procedimentos preliminares à sua participação na liga, no nosso **legítimo interesse** em manter o site seguro e, quando necessário, no cumprimento de obrigação legal.

## 5. Com quem compartilhamos

Não vendemos nem alugamos seus dados. Usamos prestadores de serviço que atuam como operadores:

- **Google** (Planilhas e Drive): armazenamento das inscrições, mensagens e imagens do site.
- **Vercel**: hospedagem do site.
- **Google Fonts**: fornecimento das fontes; ao abrir o site, seu navegador faz uma requisição aos servidores do Google.

Esses serviços podem processar dados em servidores fora do Brasil. Nesses casos, a transferência internacional ocorre com as salvaguardas oferecidas pelos próprios provedores, conforme a LGPD. Os dados também podem ser acessados pelos membros da coordenação responsáveis pela administração da liga.

## 6. Cookies

O site **não usa cookies de publicidade nem de análise de audiência**. Um cookie de sessão estritamente necessário é usado apenas por quem faz login no painel administrativo.

## 7. Por quanto tempo guardamos

Guardamos inscrições e mensagens pelo tempo necessário para cumprir as finalidades acima, em regra por até 12 meses após o fim do processo de inscrição ou do semestre letivo correspondente, salvo se a lei exigir prazo maior. Depois disso, os dados são excluídos ou anonimizados.

## 8. Seus direitos

Nos termos da LGPD, você pode solicitar a qualquer momento:

- confirmação de que tratamos seus dados e acesso a eles;
- correção de dados incompletos, inexatos ou desatualizados;
- anonimização, bloqueio ou eliminação de dados desnecessários ou tratados em desconformidade;
- portabilidade dos dados;
- informação sobre com quem compartilhamos seus dados;
- revogação do consentimento e eliminação dos dados tratados com base nele;
- oposição a tratamento que considere irregular.

Para exercer qualquer direito, escreva para [{email}](mailto:{email}). Você também pode apresentar reclamação à Autoridade Nacional de Proteção de Dados (ANPD).

## 9. Segurança

Adotamos medidas técnicas e organizacionais para proteger seus dados: conexão criptografada (HTTPS), acesso ao painel restrito por senha e número reduzido de pessoas com acesso. Nenhum sistema é totalmente imune a falhas, e trabalhamos continuamente para reduzir riscos.

## 10. Menores de idade

O site é voltado a estudantes de ensino superior. Se você tem menos de 18 anos, envie seus dados apenas com o consentimento de um responsável legal.

## 11. Alterações desta política

Podemos atualizar esta Política para refletir mudanças no site ou na lei. A data da última atualização aparece no topo desta página.

## 12. Contato

Dúvidas, solicitações ou reclamações sobre dados pessoais: [{email}](mailto:{email}).
"""

TERMS_DEFAULT = """\
## 1. Aceitação

Ao acessar e usar este site, mantido por {entidade} ("LaADS", "nós"), você concorda com estes Termos de Uso. Se não concordar, pedimos que não utilize o site.

## 2. Sobre o site

O site divulga as atividades da liga: eventos, formas de participação, parcerias e canais de contato. As informações têm caráter informativo e podem ser atualizadas a qualquer momento.

## 3. Inscrição e participação

- O envio do formulário de inscrição é uma **manifestação de interesse** e não garante vaga nem participação na liga.
- A participação segue os critérios definidos pela coordenação.
- Salvo aviso em contrário, não há taxa de inscrição.
- Você se compromete a fornecer informações verdadeiras e atualizadas.

## 4. Uso adequado

Ao usar o site, você não deve:

- enviar spam, conteúdo falso, ofensivo, discriminatório ou ilegal pelos formulários;
- tentar acessar áreas restritas, como o painel administrativo, sem autorização;
- tentar comprometer a segurança, a estabilidade ou o desempenho do site;
- coletar dados do site em massa por meios automatizados sem permissão;
- se passar por outra pessoa ou usar dados de terceiros sem autorização.

Podemos descartar envios e bloquear acessos que violem estas regras.

## 5. Eventos

Datas, horários, locais e número de vagas podem mudar sem aviso prévio. Confirme as informações no site ou pelos nossos canais antes de comparecer.

## 6. Propriedade intelectual

O nome, a marca, o layout, os textos e as imagens do site pertencem à LaADS ou são usados com autorização de seus titulares. Logos e marcas de parceiros pertencem aos respectivos donos. É proibido copiar, modificar ou distribuir esse conteúdo sem autorização prévia, salvo nos limites da lei.

## 7. Links de terceiros

O site pode conter links para páginas externas. Não controlamos nem somos responsáveis pelo conteúdo ou pelas práticas de privacidade desses sites.

## 8. Limitação de responsabilidade

Fazemos o possível para manter o site disponível e correto, mas ele é oferecido "como está", sem garantia de funcionamento ininterrupto ou livre de erros. Na extensão permitida pela lei, não nos responsabilizamos por danos decorrentes de indisponibilidade, falhas técnicas ou do uso de informações do site, sem prejuízo dos direitos garantidos por lei, inclusive pelo Código de Defesa do Consumidor, quando aplicável.

## 9. Privacidade

O tratamento de dados pessoais é descrito na [Política de Privacidade](/privacidade), parte integrante destes Termos.

## 10. Alterações

Podemos alterar estes Termos a qualquer momento. A versão vigente é a publicada nesta página, com a data da última atualização no topo. O uso do site após a alteração indica concordância com a nova versão.

## 11. Lei aplicável e foro

Estes Termos são regidos pelas leis do Brasil. Fica eleito o foro do domicílio do usuário nos casos em que a lei assim determinar e, nos demais, o foro da comarca da sede da instituição de ensino à qual a liga é vinculada.

## 12. Contato

Dúvidas sobre estes Termos: [{email}](mailto:{email}).
"""
