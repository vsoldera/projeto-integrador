Sete, primeiramente suas credencias do aws, sobreescrevendo os valores no ~/.aws/credentials.

Apos, installe a CLI do terraform: https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli

#Terminal (dentro da pasta raiz do projeto)

```terraform init```

```terraform validate```

```terraform apply```

NAO DELETE OS ARQUIVOS CRIADOS, senao vc tera de deletar tudo manualmente, e a gente sabe que ninguem quer isso :((((((

Quando estiver satisfeito com seu bom trabalho:

```terraform destroy```

Valeu, falou



Eu de volta :)

Agora temos o Airflow numa EC2, da hora demais.

Para rodar esta maravilha criada pelos deuses, entre na pasta airflow.

Antes de tudo, certifique-se de criar uma chave publica usando o seguinte comando:

```ssh-keygen -t rsa -b 4096 -f ~/.ssh/airflow-key```

Vuala, sua chave esta criada :)))))))))

Agora, apos tanto esforco, rode, do seu terminal:

```terraform init```

```terraform validate```

```terraform apply```

Assim que todos os recursos forem criados, ha a possibilidade de vc, muito provavelmente, querer logar na sua maquina EC2, desta forma, faca o seguinte:

- Va ao console do AWS, e na barra de busca, procure por EC2.
- Se vc for economico o suficiente, havera apenas uma instancia, com o nome de Airflow-EC2
- Clique na caixinha ao lado esquerdo, e depois em connect, na direita superior.
- Va na aba de SSH, e vc tera um url no seguinte formato:
```ssh -i "airflow-key.pem" ec2-user@ec2-40-221-11-249.compute-1.amazonaws.com```

- Copie o ip dessa lindeza: ```ec2-40-221-11-249.compute-1.amazonaws.com```

- Va na sua pasta .ssh, e ```ssh -i ~/.ssh/airflow-key ec2-user@ec2-40-221-11-249.compute-1.amazonaws.com```

- Se vc tiver muitos problemas e quiser dar uma olhadinha nos logs (NAO RECOMENDADO, QUEM OLHA LOGS?):

```cat /var/log/cloud-init-output.log```

Alem disso, vc pode rodar o user-data, sem precisar reiniciar a maquina infinitas vezes, altere o script em:

```/var/lib/cloud/instance/scripts/```

Ai eh so dar um bash no nome do arquivo :)