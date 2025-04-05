
## Configuração Inicial
Sete, primeiramente suas credencias do aws, sobreescrevendo os valores no `~/.aws/credentials`.
Apos, installe a CLI do terraform: https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli

## Terraform Deployment

Para evitar possíveis problemas de alguem rodar mais de uma vez o script com o mesmo nome do bucket, foi criado um arquivo **terraform.tfvars.example**. Remova do nome do arquivo a palavra **.example**, e substitua o valor padrão *your-s3-bucket* pelo nome do seu bucket.

### Terminal (dentro da pasta raiz do projeto)
```bash
terraform init
terraform validate
terraform apply
```

> ⚠️ **ATENÇÃO**: NAO DELETE OS ARQUIVOS CRIADOS, senao vc tera de deletar tudo manualmente, e a gente sabe que ninguem quer isso :((((((

Quando estiver satisfeito com seu bom trabalho:
```bash
terraform destroy
```

---

## Carregamento da base no Postgres

Primeiramente remova o **.example** do arquivo **.env.example**, após isso configure as informações do bucket e de conexão com o banco de acordo com sua infra.

```bash
pip install -r requirements.txt
python3 load_taxi_zone_on_database.py
```

## Configuração do Airflow

Agora temos o Airflow numa EC2, da hora demais.
Para rodar esta maravilha criada pelos deuses, entre na pasta airflow.

### Criação da Chave SSH
Antes de tudo, certifique-se de criar uma chave publica usando o seguinte comando:
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/airflow-key
```
Vuala, sua chave esta criada :)))))))))

### Deploy do Airflow
Agora, apos tanto esforco, rode, do seu terminal:
```bash
terraform init
terraform validate
terraform apply
```

### Conexão à Instância EC2
Assim que todos os recursos forem criados, ha a possibilidade de vc, muito provavelmente, querer logar na sua maquina EC2, desta forma, faca o seguinte:

1. Va ao console do AWS, e na barra de busca, procure por EC2.
2. Se vc for economico o suficiente, havera apenas uma instancia, com o nome de Airflow-EC2
3. Clique na caixinha ao lado esquerdo, e depois em connect, na direita superior.
4. Va na aba de SSH, e vc tera um url no seguinte formato:
   ```bash
   ssh -i "airflow-key.pem" ec2-user@ec2-40-221-11-249.compute-1.amazonaws.com
   ```
5. Copie o ip dessa lindeza: `ec2-40-221-11-249.compute-1.amazonaws.com`
6. Va na sua pasta .ssh, e execute:
   ```bash
   ssh -i ~/.ssh/airflow-key ec2-user@ec2-40-221-11-249.compute-1.amazonaws.com
   ```

### Rodando o Pyspark via Jupyter Notebook

#### Instalação do Pyspark e configução no Jupyter

```bash
wget https://downloads.apache.org/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz
tar -xvzf spark-3.5.0-bin-hadoop3.tgz
sudo mv spark-3.5.0-bin-hadoop3 /opt/spark

export SPARK_HOME=/opt/spark
export PATH=$SPARK_HOME/bin:$PATH
export PYSPARK_PYTHON=python3
export PYSPARK_DRIVER_PYTHON=jupyter
export PYSPARK_DRIVER_PYTHON_OPTS="notebook"
source ~/.bashrc
```

#### Rodando o pyspark

Primeiro faça o download localmente do **jar** do PostgresSQL

```bash
wget https://jdbc.postgresql.org/download/postgresql-42.7.2.jar -P ~/jars/
```

Depois rode passando os seguintes paramêtros:

```bash
pyspark --packages org.apache.hadoop:hadoop-aws:3.3.1,com.amazonaws:aws-java-sdk-bundle:1.11.901 --jars ~/jars/postgresql-42.7.2.jar
```

### Troubleshooting
Se vc tiver muitos problemas e quiser dar uma olhadinha nos logs (NAO RECOMENDADO, QUEM OLHA LOGS?):
```bash
cat /var/log/cloud-init-output.log
```

Alem disso, vc pode rodar o user-data, sem precisar reiniciar a maquina infinitas vezes, altere o script em:
```bash
/var/lib/cloud/instance/scripts/
```

Ai eh so dar um bash no nome do arquivo :)

Nao esquece do destroy quando terminar:

```terraform destroy```




## Airflow testing

- Adicionar script silver ao s3: aws s3 cp script_silver.py s3://taxi-raw-grupo-5/scripts/process_taxi_data.py

- Adicionar o emr-py para dentro do container airflow: docker cp emr-dag.py container_id:/opt/airflow/dags

- Permissao do S3? Desativar encriptacao

- python -m pip install --upgrade pip

- set java version:

curl -L https://corretto.aws/downloads/latest/amazon-corretto-8-x64-linux-jdk.tar.gz -o corretto-8-linux.tar.gz

export JAVA_HOME=~/java/amazon-corretto-8.442.06.1-linux-x64/

export PATH=$JAVA_HOME/bin:$PATH