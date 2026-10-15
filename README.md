# Herdeiros de Israel — etapa 1: autenticação real

Este projeto **não é a versão completa**. Ele implementa login real, senhas com hash, sessões em cookie HttpOnly/Secure/SameSite, proteção CSRF, banco PostgreSQL, papéis e cadastro/edição de usuários pelo diretor. As telas de classes, frequência, secretaria e calendário ainda não estão implementadas. Não armazene dados de menores antes de concluir a revisão de segurança e privacidade.

## Publicação no Render

1. Crie um banco **Postgres** no Render, anote a **Internal Database URL**.
2. Envie os **arquivos desta pasta (não apenas o ZIP)** para um repositório GitHub separado do GitHub Pages, por exemplo `sistema-herdeiros-real`.
3. No Render, crie um **Web Service** conectado ao repositório.
4. Runtime Python. Build Command: `pip install -r requirements.txt`.
5. Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app`.
6. Environment Variables (marque como secretas):
   - `DATABASE_URL`: URL interna do PostgreSQL
   - `SECRET_KEY`: segredo aleatório longo, diferente da senha
   - `ADMIN_EMAIL`: e-mail do diretor
   - `ADMIN_PASSWORD`: senha inicial forte com pelo menos 12 caracteres
   - `COOKIE_SECURE`: `1` (produção HTTPS)
7. Faça o deploy. O banco cria as tabelas automaticamente e cria o primeiro diretor **apenas se não houver outro diretor**. Após a primeira inicialização, retire `ADMIN_PASSWORD` do ambiente. Para alterar senha depois, use a tela de usuários.

**Atenção:** não coloque senhas nem URLs de banco no GitHub. Nunca use GitHub Pages para hospedar este backend. Este MVP não possui ainda recuperação de senha, bloqueio de tentativas, trilha de auditoria, MFA, migrações de esquema, nem políticas completas para tratamento de dados de crianças. Essas medidas devem ser adicionadas antes do uso real pelo clube.
