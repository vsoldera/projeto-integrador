#!/bin/sh

if [ -z "$1" ]; then
    echo "Usage: $0 <BUCKET_ID>"
    exit 1
fi

BUCKET_ID="$1"

for year in {2018}; do
    for month in {01..02}; do
        filename="yellow_tripdata_${year}-${month}.parquet"
        s3_path="s3://$BUCKET_ID/$filename"

        if aws s3 ls "$s3_path" > /dev/null 2>&1; then
            echo "Arquivo $filename já existe no S3. Pulando download e upload."
        else
            curl -o "$filename" "https://d37ci6vzurychx.cloudfront.net/trip-data/$filename"
            
            if [ -f "$filename" ]; then
                aws s3 cp "$filename" "s3://$BUCKET_ID/"
                echo "Finished uploading data for ${year} and ${month}: ${filename}"
            else
                echo "Erro ao baixar o arquivo $filename. Pulando upload."
            fi
        fi
    done
done

curl -o taxi_zone_lookup.csv https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
if [ -f "taxi_zone_lookup.csv" ]; then
    aws s3 cp taxi_zone_lookup.csv "s3://$BUCKET_ID/"
    echo "Finished uploading taxi_zone_lookup.csv."
else
    echo "Erro ao baixar taxi_zone_lookup.csv. Pulando upload."
fi
