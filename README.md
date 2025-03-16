# AWS Terraform & Airflow Setup Guide

## Configuração Inicial
Sete, primeiramente suas credencias do aws, sobreescrevendo os valores no `~/.aws/credentials`.
Apos, installe a CLI do terraform: https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli

## Terraform Deployment
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

## Configuração do Airflow
Eu de volta :)
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
