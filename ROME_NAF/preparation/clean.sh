nom=$1

#if [ ! -f ${nom}.csv.bz2 ]; then
if [ ! -f ${nom}.csv.gz ]; then
    echo "Pas trouvé !"
    exit 1
fi

echo "Décompression..."
#bzip2 -d ${nom}.csv.bz2
gunzip ${nom}.csv.gz
echo "...fait"

echo "Suppression des guillemets..."
cat ${nom}.csv | sed 's/.$//' | sed 's/^.//' > ${nom}_sans_guillemets.csv
echo "...fait"

echo "Changement de séparateurs..."
cat ${nom}_sans_guillemets.csv | sed 's/\xc2\xa5/\|/g' > ${nom}_sep.csv
echo "...fait"

echo "Creation d'un échantillon..."
awk 'NR == 1 || NR % 1000 == 0' ${nom}_sep.csv > ${nom}_sample.csv
echo "...fait"
