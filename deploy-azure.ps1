param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$ContainerAppEnvironmentName,
    
    [Parameter(Mandatory=$true)]
    [string]$ContainerAppName,
    
    [Parameter(Mandatory=$true)]
    [string]$ContainerRegistryName,
    
    [Parameter(Mandatory=$true)]
    [string]$VNetName,
    
    [Parameter(Mandatory=$true)]
    [string]$SubnetName,
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "East US",
    
    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest",
    
    [Parameter(Mandatory=$true)]
    [string]$SapBaseUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$SapCompanyDb,
    
    [Parameter(Mandatory=$true)]
    [string]$SapUsername,
    
    [Parameter(Mandatory=$true)]
    [string]$SapPassword
)

Write-Host " Iniciando despliegue de servidor MCP SAP en Azure Container Apps..." -ForegroundColor Green
Write-Host " IMPORTANTE: Este script requiere credenciales SAP como parámetros por seguridad" -ForegroundColor Yellow
Write-Host " Ejemplo de uso:" -ForegroundColor Cyan
Write-Host " .\deploy-azure.ps1 -ResourceGroupName 'rg-mcp-sap' -ContainerAppEnvironmentName 'cae-mcp-sap' -ContainerAppName 'app-sap-mcp' -ContainerRegistryName 'acrmcpsap' -VNetName 'vnet-mcp-sap' -SubnetName 'subnet-container-apps' -SapBaseUrl 'https://your-sap:50000/b1s/v2' -SapCompanyDb 'YOUR_DB' -SapUsername 'your_user' -SapPassword 'your_password'" -ForegroundColor Cyan

# Variables
$ImageName = "sap-mcp-server"
$FullImageName = "$ContainerRegistryName.azurecr.io/$ImageName`:$ImageTag"

try {
    # 1. Verificar login en Azure
    Write-Host "Verificando autenticación Azure..." -ForegroundColor Yellow
    $context = az account show --query "name" -o tsv 2>$null
    if (!$context) {
        Write-Host "No estás autenticado en Azure. Ejecuta: az login" -ForegroundColor Red
        exit 1
    }
    Write-Host "Autenticado en Azure: $context" -ForegroundColor Green

    # 2. Crear resource group si no existe
    Write-Host "Verificando Resource Group..." -ForegroundColor Yellow
    $rgExists = az group exists --name $ResourceGroupName
    if ($rgExists -eq "false") {
        Write-Host "Creando Resource Group: $ResourceGroupName" -ForegroundColor Yellow
        az group create --name $ResourceGroupName --location $Location
    }
    Write-Host "Resource Group listo: $ResourceGroupName" -ForegroundColor Green

    # 3. Crear Container Registry si no existe
    Write-Host "Verificando Container Registry..." -ForegroundColor Yellow
    $acrExists = az acr show --name $ContainerRegistryName --resource-group $ResourceGroupName 2>$null
    if (!$acrExists) {
        Write-Host "Creando Container Registry: $ContainerRegistryName" -ForegroundColor Yellow
        az acr create --resource-group $ResourceGroupName --name $ContainerRegistryName --sku Basic --admin-enabled true
    }
    Write-Host "Container Registry listo: $ContainerRegistryName" -ForegroundColor Green

    # 4. Build y push de la imagen
    Write-Host "Construyendo imagen Docker..." -ForegroundColor Yellow
    az acr build --registry $ContainerRegistryName --image "$ImageName`:$ImageTag" .
    Write-Host "Imagen construida y subida: $FullImageName" -ForegroundColor Green

    # 5. Crear VNet y Subnet si no existen
    Write-Host "Verificando VNet..." -ForegroundColor Yellow
    $vnetExists = az network vnet show --name $VNetName --resource-group $ResourceGroupName 2>$null
    if (!$vnetExists) {
        Write-Host "Creando VNet: $VNetName" -ForegroundColor Yellow
        az network vnet create `
            --name $VNetName `
            --resource-group $ResourceGroupName `
            --location $Location `
            --address-prefixes "10.0.0.0/16"
        Write-Host "VNet creada: $VNetName" -ForegroundColor Green
    }

    # Verificar/crear subnet para Container Apps
    Write-Host "Verificando Subnet..." -ForegroundColor Yellow
    $subnetExists = az network vnet subnet show --resource-group $ResourceGroupName --vnet-name $VNetName --name $SubnetName 2>$null
    if (!$subnetExists) {
        Write-Host "Creando Subnet: $SubnetName" -ForegroundColor Yellow
        az network vnet subnet create `
            --name $SubnetName `
            --resource-group $ResourceGroupName `
            --vnet-name $VNetName `
            --address-prefixes "10.0.1.0/24" `
            --delegations "Microsoft.App/environments"
        Write-Host "Subnet creada: $SubnetName" -ForegroundColor Green
    }

    # Obtener subnet ID
    Write-Host "Obteniendo información de Subnet..." -ForegroundColor Yellow
    $subnetId = az network vnet subnet show --resource-group $ResourceGroupName --vnet-name $VNetName --name $SubnetName --query "id" -o tsv
    if (!$subnetId) {
        Write-Host "No se pudo obtener el ID de la subnet $SubnetName" -ForegroundColor Red
        exit 1
    }
    Write-Host "Subnet configurada: $SubnetName" -ForegroundColor Green

    # 6. Crear Container App Environment con VNet
    Write-Host "Verificando Container App Environment..." -ForegroundColor Yellow
    $envExists = az containerapp env show --name $ContainerAppEnvironmentName --resource-group $ResourceGroupName 2>$null
    if (!$envExists) {
        Write-Host "Creando Container App Environment con VNet..." -ForegroundColor Yellow
        az containerapp env create `
            --name $ContainerAppEnvironmentName `
            --resource-group $ResourceGroupName `
            --location $Location `
            --infrastructure-subnet-resource-id $subnetId
    }
    Write-Host "Container App Environment listo: $ContainerAppEnvironmentName" -ForegroundColor Green

    # 7. Crear/actualizar Container App
    Write-Host "Desplegando Container App..." -ForegroundColor Yellow
    
    # Crear el Container App con configuración MCP
    az containerapp create `
        --name $ContainerAppName `
        --resource-group $ResourceGroupName `
        --environment $ContainerAppEnvironmentName `
        --image $FullImageName `
        --registry-server "$ContainerRegistryName.azurecr.io" `
        --cpu 0.5 `
        --memory 1Gi `
        --min-replicas 1 `
        --max-replicas 3 `
        --ingress external `
        --target-port 8000 `
        --env-vars "LOG_LEVEL=INFO" "PYTHONUNBUFFERED=1" `
        --secrets "sap-base-url=$SapBaseUrl" "sap-company-db=$SapCompanyDb" "sap-username=$SapUsername" "sap-password=$SapPassword" `
        --env-vars "SAP_BASE_URL=secretref:sap-base-url" "SAP_COMPANY_DB=secretref:sap-company-db" "SAP_USERNAME=secretref:sap-username" "SAP_PASSWORD=secretref:sap-password"

    Write-Host "Container App desplegado: $ContainerAppName" -ForegroundColor Green

    # 8. Mostrar información del despliegue
    Write-Host "`n Información del despliegue:" -ForegroundColor Cyan
    Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor White
    Write-Host "Container Registry: $ContainerRegistryName.azurecr.io" -ForegroundColor White
    Write-Host "Container App: $ContainerAppName" -ForegroundColor White
    Write-Host "Environment: $ContainerAppEnvironmentName" -ForegroundColor White
    Write-Host "Imagen: $FullImageName" -ForegroundColor White
    Write-Host "VNet: $VNetName" -ForegroundColor White
    Write-Host "Subnet: $SubnetName" -ForegroundColor White

    # 9. Obtener URL del Container App
    $appUrl = az containerapp show --name $ContainerAppName --resource-group $ResourceGroupName --query "properties.configuration.ingress.fqdn" -o tsv
    if ($appUrl) {
        Write-Host "`n URL de la aplicación: https://$appUrl" -ForegroundColor Green
    }

    Write-Host "`n ¡Despliegue completado exitosamente!" -ForegroundColor Green
    Write-Host "Para ver logs: az containerapp logs show --name $ContainerAppName --resource-group $ResourceGroupName" -ForegroundColor Cyan

} catch {
    Write-Host "Error durante el despliegue: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

