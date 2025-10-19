# ECON847_PS2
UNC Empirical IO I, F25: Problem Set 2

## Overview
In this problem set, we will construct and estimate a structural demand/supply model and perform a counterfactual using [Dominick’s Scanner Data](https://www.chicagobooth.edu/research/kilts/research-data/dominicks), cigarettes category.

## How to read unique_upccig_hardcoded.csv

* Generic: no brand in DESCRIP
* Value: considered "cheap". Does not imply Generic, nor is implied by Generic. William Penn and Doral are value bc that's the brand reputation. The generics are not "value" unless otherwise stated in the DESCRIP (triggered by: "value", "discount", "$")
* Premium: marketed as premium. Triggered by: "prem", "select", "special"
* We assume Generic -> not flavored unless otherwise stated, or colored package
* Menthol/Flavored: Create the "possibly" for brands that have both varieties. 
* Assume that black-packaged cigarettes are flavored, following industry convention
*  "Implied discount": assuming each buyer takes full advantage of the offer, actual_price = (1-implied_discount)*stricker price. Applies only to CIGARETTES B3G2F,CHINA BLK WHISKEY B1, CHINA BLK FIRE B1G1.
*  * Does NOT include explicit discounts, such as MERIT ILT $5 OFF

## How to read unique_upccig_hardcoded.csv

* Variables unique to unique_upccig_hardcoded.csv: above
* Generic: kept both, denoted Generic_hardcoded or Generic_automated. The former means that there is no recognizable brand. The latter that there is no recognizable brand matching one of the 2 FTC reports. These are not the same things: all the non-cigarette products can be branded (so Generic_hardcoded==0) but not be present in the report (Generic_automated==1)
* Menthol: the automatic aggregation for menthol was clearly too conservative as no product was reported having menthol, so I discarded it in favor of the hardcoded one. The "flavored" column in more relevant anyway

## Group Members
- Jiabing Liu
- Francesco Slataper
