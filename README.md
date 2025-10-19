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

## Group Members
- Jiabing Liu
- Francesco Slataper
