# SAP Business One MCP Server

# SAP Business One MCP Server

Servidor MCP (Model Context Protocol) para integrar SAP Business One con Microsoft Copilot Studio.

## 🚀 Características

- **Conexión persistente** a SAP Business One Service Layer API
- **Creación de Sales Orders** con validación completa
- **Protocolo MCP Streamable** compatible con Microsoft Copilot Studio
- **Deployment en Azure Container Apps** listo para producción

## 🛠️ Herramientas Disponibles

1. **sap_connect** - Conectar a SAP Business One
2. **sap_status** - Verificar estado de conexión
3. **sap_create_sales_order** - Crear Sales Orders

## 📋 Requisitos

- Python 3.11+
- SAP Business One con Service Layer habilitado
- Variables de entorno configuradas

## ⚙️ Configuración

1. Copiar `.env.example` a `.env`:
```bash
cp .env.example .env
```

2. Configurar variables de entorno en `.env`:
```
SAP_BASE_URL=https://your-sap-server:50000/b1s/v2
SAP_COMPANY_DB=YOUR_DB
SAP_USERNAME=your_user
SAP_PASSWORD=your_password
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecutar servidor:
```bash
python server.py
```

## 🔗 Integración con Microsoft Copilot Studio

### 1. Schema File
Usar `sap-mcp-schema.yaml` como archivo de schema OpenAPI en Copilot Studio.

### 2. Crear Custom Connector
1. En Copilot Studio, ir a **Tools** → **Add a tool** → **New tool** → **Custom connector**
2. Seleccionar **Import OpenAPI file**
3. Subir el archivo `sap-mcp-schema.yaml`
4. Completar la configuración siguiendo la [documentación oficial](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)

### 3. Configurar Host
Actualizar el `host` en `sap-mcp-schema.yaml`:
- Para desarrollo local: `localhost:8000`
- Para producción: `your-domain.azurecontainerapps.io`

## 🐳 Deployment

### Azure Container Apps

1. Configurar variables de entorno en Azure:
```bash
az containerapp env set-vars --name myapp-env --resource-group myresourcegroup --vars SAP_BASE_URL=https://your-sap-server:50000/b1s/v2 SAP_COMPANY_DB=YOUR_DB SAP_USERNAME=your_user SAP_PASSWORD=your_password
```

2. Deploy usando el script:
```bash
./deploy-azure.ps1
```

### Docker

```bash
docker build -t sap-mcp-server .
docker run -p 8000:8000 --env-file .env sap-mcp-server
```

## 📊 Ejemplo de Uso

### Crear Sales Order
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "sap_create_sales_order",
    "arguments": {
      "CardCode": "CUSTOMER_CODE",
      "DocDueDate": "YYYYMMDD",
      "DocCurrency": "USD",
      "DocRate": 1.0,
      "DocumentLines": [
        {
          "ItemCode": "ITEM_CODE",
          "Quantity": "1",
          "TaxCode": "TAX_CODE",
          "UnitPrice": "100.00"
        }
      ]
    }
  }
}
```

### Respuesta
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "✅ Sales Order creada exitosamente:
{
  \"status\": \"success\",
  \"DocEntry\": 12345,
  \"DocNum\": 1001,
  \"CardCode\": \"CUSTOMER_CODE\",
  \"CardName\": \"Customer Name\",
  \"DocTotal\": 1000.0,
  \"DocCurrency\": \"USD\",
  \"DocRate\": 1.0
}"
      }
    ]
  }
}
```

## 🔍 Health Check

```bash
curl http://localhost:8000/health
```

## 📄 Licencia

MIT License

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 🎯 Objetivo

Exponer herramientas de SAP Business One Service Layer API mediante el protocolo MCP streamable para que Microsoft Copilot Studio pueda consumirlas como un custom connector.

## 🏗️ Arquitectura

```
Microsoft Copilot Studio
    ↓ (HTTPS/JSON-RPC)
Azure Container Apps (Public Endpoint)
    ↓ (Service Layer API)
SAP Business One Server
```

## � Características

### Herramientas MCP Disponibles

- **`sap_connect`**: Conectar a SAP Business One
- **`sap_status`**: Verificar estado de conexión
- **`sap_create_sales_order`**: Crear Sales Orders con validación completa

### Recursos MCP Disponibles

- **`sap://status`**: Estado actual de la conexión SAP

### Endpoints HTTP

- **`POST /mcp`**: Endpoint principal para protocolo MCP streamable
- **`GET /health`**: Verificación de salud del servidor

## 🛠️ Configuración

### 1. Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

Completa las variables:

```env
# SAP Business One Service Layer
SAP_BASE_URL=https://your-sap-server:50000/b1s/v1
SAP_COMPANY_DB=YOUR_COMPANY_DB
SAP_USERNAME=your_username
SAP_PASSWORD=your-password
```

### 2. Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python server.py
```

El servidor estará disponible en `http://localhost:8000`

### 3. Probar Localmente

```bash
# Verificar salud del servidor
curl http://localhost:8000/health

# Probar herramientas MCP
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## ☁️ Despliegue en Azure

### Prerequisitos

- Azure CLI instalado y configurado
- Azure Container Registry creado
- Permisos para crear Container Apps

### Despliegue Automatizado

```powershell
# Ejecutar script de despliegue
.\deploy-azure.ps1 -ResourceGroupName "rg-mcp-sap" `
                   -ContainerAppEnvironmentName "cae-mcp-sap" `
                   -ContainerAppName "app-sap-mcp" `
                   -ContainerRegistryName "acrmcpsap" `
                   -VNetName "vnet-mcp-sap" `
                   -SubnetName "subnet-container-apps"
```

### Configurar Secrets en Azure

```bash
# Variables de entorno en Container App
az containerapp secret set --name app-sap-mcp --resource-group rg-mcp-sap \
  --secrets sap-base-url="https://your-sap:50000/b1s/v1" \
            sap-company-db="YOUR_COMPANY_DB" \
            sap-username="your_username" \
            sap-password="your-password"
```

## 🔌 Integración con Copilot Studio

### 1. Crear Custom Connector

1. Ir a **Power Platform Admin Center**
2. Seleccionar **Custom Connectors** → **New custom connector** → **Import from OpenAPI file**
3. Subir el archivo `sap-mcp-schema.yaml`
4. Configurar la URL del host con tu Container App:
   ```
   https://app-sap-mcp-test.bravewater-b67ade29.eastus.azurecontainerapps.io
   ```

### 2. Configurar en Copilot Studio

1. Abrir **Copilot Studio**
2. Ir a **Settings** → **Generative AI** → **Custom Actions**
3. Agregar el custom connector creado
4. Las herramientas SAP aparecerán automáticamente como acciones disponibles

### 3. Ejemplo de Uso en Copilot

```
Usuario: "Conecta a SAP y crea una orden de venta"

Copilot ejecutará:
1. sap_connect() - para conectar
2. sap_create_sales_order(CardCode="CUSTOMER", DocumentLines=[...]) - para crear la orden
```

## 🧪 Pruebas del Protocolo MCP

### Ejemplo de Solicitud MCP

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "sap_create_sales_order",
    "arguments": {
      "CardCode": "CUSTOMER_CODE",
      "DocumentLines": [
        {
          "ItemCode": "ITEM_CODE",
          "Quantity": "1",
          "UnitPrice": "100.00"
        }
      ]
    }
  },
  "id": 1
}
```

### Ejemplo de Respuesta MCP

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "✅ Sales Order creada exitosamente: DocEntry 12345"
      }
    ]
  }
}
```

## 📁 Estructura del Proyecto

```
MCP-SAP-main/
├── server.py               # Servidor MCP principal con FastAPI
├── sap_client.py           # Cliente para SAP Business One Service Layer
├── sap-mcp-schema.yaml     # Schema OpenAPI para Custom Connector
├── deploy-azure.ps1        # Script de despliegue en Azure
├── Dockerfile              # Imagen de contenedor
├── requirements.txt        # Dependencias Python
├── .env.example           # Plantilla de configuración
├── azure-container-app.yaml # Configuración de Container App
└── README.md              # Este archivo
```

## 🔧 Desarrollo

### Agregar Nueva Herramienta

1. Definir en `handle_list_tools()`:
```python
Tool(
    name="nueva_herramienta",
    description="Descripción de la herramienta",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "Parámetro"}
        },
        "required": ["param1"]
    }
)
```

2. Implementar en `handle_call_tool()`:
```python
elif name == "nueva_herramienta":
    # Lógica de la herramienta
    return [TextContent(type="text", text="Resultado")]
```

## 🔍 Troubleshooting

### Problemas Comunes

1. **Error de conexión SAP**:
   - Verificar variables de entorno
   - Comprobar conectividad de red
   - Validar credenciales

2. **Container App no responde**:
   - Verificar logs: `az containerapp logs show --name app-sap-mcp --resource-group rg-mcp-sap`
   - Comprobar variables de entorno en Azure

3. **Copilot Studio no encuentra herramientas**:
   - Verificar schema OpenAPI
   - Comprobar URL del host en custom connector
   - Validar protocolo `mcp-streamable-1.0`

### Logs y Debugging

```bash
# Ver logs locales
python server.py  # Logs aparecen en consola

# Ver logs en Azure
az containerapp logs show --name app-sap-mcp --resource-group rg-mcp-sap --follow

# Probar endpoints manualmente
curl https://your-container-app.azurecontainerapps.io/health
curl -X POST https://your-container-app.azurecontainerapps.io/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## 📚 Referencias

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [SAP Business One Service Layer API](https://help.sap.com/docs/SAP_BUSINESS_ONE/68a2e87fb29941b5bf959a184d9c6727/16f20002dd5645ad84f3853d08e76a0f.html)
- [Microsoft Copilot Studio Custom Connectors](https://docs.microsoft.com/en-us/connectors/custom-connectors/)
- [Azure Container Apps](https://docs.microsoft.com/en-us/azure/container-apps/)

## 🤝 Contribución

1. Fork el repositorio
2. Crear rama feature: `git checkout -b feature/nueva-caracteristica`
3. Commit cambios: `git commit -am 'Agregar nueva característica'`
4. Push a la rama: `git push origin feature/nueva-caracteristica`
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🆘 Soporte

- **Issues**: [GitHub Issues](https://github.com/NXr10/MCP-SAP/issues)
- **Documentación**: [Wiki del proyecto](https://github.com/NXr10/MCP-SAP/wiki)
- **Contacto**: Crear un issue para soporte técnico
    --secrets "sap-username=tu-usuario" "sap-password=tu-password"
```

## 🔧 Configuración Manual

### Crear VNet y Subnet (si no existe)

```bash
# Crear VNet
az network vnet create \
    --resource-group $ResourceGroupName \
    --name $VNetName \
    --address-prefix 10.0.0.0/16 \
    --subnet-name $SubnetName \
    --subnet-prefix 10.0.1.0/24

# Delegación para Container Apps
az network vnet subnet update \
    --resource-group $ResourceGroupName \
    --vnet-name $VNetName \
    --name $SubnetName \
    --delegations Microsoft.App/environments
```

### Configurar NSG para SAP

```bash
# Crear regla para permitir tráfico a SAP
az network nsg rule create \
    --resource-group $ResourceGroupName \
    --nsg-name nsg-containers \
    --name AllowSAP \
    --priority 100 \
    --direction Outbound \
    --access Allow \
    --protocol Tcp \
    --destination-port-ranges 50000 \
    --destination-address-prefixes 10.0.0.0/16
```

## 📊 Verificación

### Ver logs de la aplicación

```bash
az containerapp logs show \
    --name $ContainerAppName \
    --resource-group $ResourceGroupName \
    --follow
```

### Verificar conectividad

```bash
# Entrar al contenedor para debug
az containerapp exec \
    --name $ContainerAppName \
    --resource-group $ResourceGroupName

# Verificar variables de entorno
echo $SAP_BASE_URL
```

## 🔐 Seguridad

### Variables de entorno configuradas:

- `SAP_BASE_URL`: URL de tu SAP Business One API
- `SAP_COMPANY_DB`: Base de datos de la compañía
- `SAP_USERNAME`: Usuario SAP
- `SAP_PASSWORD`: Contraseña SAP (almacenada como secreto)

### Mejores prácticas:

- Credenciales almacenadas como secretos de Container Apps
- VNet isolation para comunicación privada con SAP
- Contenedor ejecutándose con usuario no-root
- Recursos limitados (CPU/Memory)

## 🛠️ Troubleshooting

### Error de conectividad a SAP

1. Verificar que SAP esté ejecutándose
2. Verificar NSG rules
3. Verificar que las IPs sean correctas
4. Verificar credenciales

### Error de despliegue

1. Verificar permisos en Azure
2. Verificar que el nombre del Container Registry sea único
3. Verificar que la VNet exista

### Ver logs detallados

```bash
az containerapp logs show \
    --name $ContainerAppName \
    --resource-group $ResourceGroupName \
    --type console
```

## 📞 Soporte

Para problemas específicos:

1. Revisar logs de Container Apps
2. Verificar conectividad de red
3. Probar credenciales SAP desde Postman
4. Verificar configuración de secretos

## 🔄 Actualizaciones

Para actualizar la aplicación:

```bash
# Rebuild y redeploy
az acr build --registry $ContainerRegistryName --image "sap-mcp-server:latest" .

# Restart container app
az containerapp revision restart \
    --name $ContainerAppName \
    --resource-group $ResourceGroupName
```
