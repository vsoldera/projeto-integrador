Sete, primeiramente suas credencias do aws, sobreescrevendo os valores no ~/.aws/credentials.

Apos, installe a CLI do terraform: https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli

# Terminal (dentro da pasta raiz do projeto)

Para evitar possíveis problemas de alguem rodar mais de uma vez o script com o mesmo nome do bucket, foi criado um arquivo **terraform.tfvars.example**. Remova do nome do arquivo a palavra **.example**, e substitua o valor padrão *your-s3-bucket* pelo nome do seu bucket.

```terraform init```

```terraform validate```

```terraform apply```

NAO DELETE OS ARQUIVOS CRIADOS, senao vc tera de deletar tudo manualmente, e a gente sabe que ninguem quer isso :((((((

Quando estiver satisfeito com seu bom trabalho:

```terraform destroy```

# Carregamento da base no Postgres

Primeiramente remova o **.example** do arquivo **.env.example**, após isso configure as informações do bucket e de conexão com o banco de acordo com sua infra.

```pip install -r requirements.txt```

```python3 load_taxi_zone_on_database.py```

Valeu, falou