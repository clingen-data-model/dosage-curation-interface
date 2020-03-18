#!/bin/bash
shopt -s expand_aliases

# change these if you want a different logging output
alias eprint="logger -p 3 -s -t dci"
alias nprint="logger -p 5 -s -t dci"

run_date=`date +"%m-%d-%y"`
log_file=log/$run_date.log

#source ../clingen_env/bin/activate
echo "Making FTP files" >> $log_file;
python3 MakeFTPFiles.py >> $log_file
wait

nprint "FTP file generation completed"j

# filter out any not yet evaluated messaged
grep -v "Not yet evaluated" ClinGen_triplosensitivity_gene_GRCh37.bed > ClinGen_triplosensitivity_gene_GRCh37.bed.tmp
grep -v "Not yet evaluated" ClinGen_haploinsufficiency_gene_GRCh37.bed > ClinGen_haploinsufficiency_gene_GRCh37.bed.tmp
grep -v "Not yet evaluated" ClinGen_region_curation_list_GRCh37.tsv > ClinGen_region_curation_list_GRCh37.tsv.tmp
grep -v "Not yet evaluated" ClinGen_gene_curation_list_GRCh37.tsv > ClinGen_gene_curation_list_GRCh37.tsv.tmp
grep -v "Not yet evaluated" ClinGen_triplosensitivity_gene_GRCh38.bed > ClinGen_triplosensitivity_gene_GRCh38.bed.tmp
grep -v "Not yet evaluated" ClinGen_haploinsufficiency_gene_GRCh38.bed > ClinGen_haploinsufficiency_gene_GRCh38.bed.tmp
grep -v "Not yet evaluated" ClinGen_region_curation_list_GRCh38.tsv > ClinGen_region_curation_list_GRCh38.tsv.tmp
grep -v "Not yet evaluated" ClinGen_gene_curation_list_GRCh38.tsv > ClinGen_gene_curation_list_GRCh38.tsv.tmp

mv ClinGen_triplosensitivity_gene_GRCh37.bed.tmp ftp_staging/ClinGen_triplosensitivity_gene_GRCh37.bed
mv ClinGen_haploinsufficiency_gene_GRCh37.bed.tmp ftp_staging/ClinGen_haploinsufficiency_gene_GRCh37.bed
mv ClinGen_region_curation_list_GRCh37.tsv.tmp ftp_staging/ClinGen_region_curation_list_GRCh37.tsv
mv ClinGen_gene_curation_list_GRCh37.tsv.tmp ftp_staging/ClinGen_gene_curation_list_GRCh37.tsv
mv ClinGen_triplosensitivity_gene_GRCh38.bed.tmp ftp_staging/ClinGen_triplosensitivity_gene_GRCh38.bed
mv ClinGen_haploinsufficiency_gene_GRCh38.bed.tmp ftp_staging/ClinGen_haploinsufficiency_gene_GRCh38.bed
mv ClinGen_region_curation_list_GRCh38.tsv.tmp ftp_staging/ClinGen_region_curation_list_GRCh38.tsv
mv ClinGen_gene_curation_list_GRCh38.tsv.tmp ftp_staging/ClinGen_gene_curation_list_GRCh38.tsv
rm *.tmp *.bed *.tsv


echo "Running IndexRegions2IDs.py" >> $log_file;
python3 IndexRegions2IDs.py  >> $log_file
if [ $? != 0 ]; then
	eprint "DCI SCRIPT ERROR:  Region Index failed"
fi

echo "Running IndexNames2IDs.py" >> $log_file;
python3 IndexNames2IDs.py  >> $log_file
if [ $? != 0 ]; then
	eprint "DCI SCRIPT ERROR:  Names Index failed"
fi

echo "Running ProcessGeneDaily.py" >> $log_file;
python3 ProcessGeneDaily.py >> $log_file;
if [ $? != 0 ]; then
	eprint "DCI SCRIPT ERROR:  Gene Daily failed"
fi

echo "Running ratingChange.py" >> $log_file
python3 ratingChange.py >> $log_file
if [ $? != 0 ]; then
	eprint "DCI SCRIPT ERROR:  Rating Change failed"
fi

echo "Running acmg56_curation.py" >> $log_file
python3 acmg56_curation.py >> $log_file
if [ $? != 0 ]; then
	eprint "DCI SCRIPT ERROR:  ACMG56 Curation failed"
fi

echo "Running pathogenic_region.py" >> $log_file
python3 pathogenic_region.py >> $log_file
if [ $? != 0 ]; then
	eprint "DCI SCRIPT ERROR:  Pathogenic Region failed"
fi

echo "Running attribute_check.py" >> $log_file
python3 attribute_check.py >> $log_file
if [ $? != 0 ]; then
	eprint "DCI SCRIPT ERROR:  Attribute Check failed"
fi

echo "Running recent_review.py" >> $log_file
python3 recent_review.py >> $log_file
if [ $? != 0 ]; then
	eprint "DCI SCRIPT ERROR:  Recent Review failed"
fi

wait 

mv region.idx daily_staging
mv gene_overlap.idx daily_staging
mv gene_isca.idx daily_staging
mv stats.html daily_staging
mv ratingchange.html daily_staging 
mv acmg56_body.html daily_staging
mv pathogenic_region_body.html daily_staging
# mv ISCA_Gene.txt  autocomplete/   // This is used by autocomplete in index page about gene_name input
# mv mim_mimnames_cui_gtrname.tsv daily_staging/mim_mimnames_cui_gtrname.tsv // this is a file I need to check
mv recent_review.html daily_staging
mv stat_*.html daily_staging/stat/

# copy the ftp files to the public area
yesterday=`date -d "1 day ago" '+%Y%m%d'`

mkdir /var/ftp/clingen/archive/${yesterday}
cp /var/ftp/clingen/* /var/ftp/clingen/archive/${yesterday}
cp /var/www/dosage/daily_process/ftp_staging/* /var/ftp/clingen

# copy the daily files to the docroot area
mkdir /var/www/dosage/daily/archive/${yesterday}
cp /var/www/dosage/daily/* /var/www/dosage/daily/archive/${yesterday}
cp -R /var/www/dosage/daily_process/daily_staging/* /var/www/dosage/daily

nprint "DCI SCRIPT: Successfully Completed"
