param([Parameter(Mandatory=$true)][string]$ResourceGroup,[Parameter(Mandatory=$true)][string]$ApiImage,[Parameter(Mandatory=$true)][string]$WebImage,[Parameter(Mandatory=$true)][string]$CorsOrigins)
az deployment group create --resource-group $ResourceGroup --template-file "$PSScriptRoot/main.bicep" --parameters apiImage=$ApiImage webImage=$WebImage corsOrigins=$CorsOrigins
