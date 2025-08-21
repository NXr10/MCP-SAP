#!/usr/bin/env python3
"""
Servidor MCP HTTP para SAP Business One con gestión de sesión persistente
"""

import os
import json
import logging
from typing import Any, Sequence
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from sap_client import SAPClient

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variable global para cliente SAP
sap_client = None

def get_sap_client():
    """Obtener cliente SAP con gestión de sesión persistente"""
    global sap_client
    
    try:
        # Si no hay cliente, crear uno nuevo
        if sap_client is None:
            sap_client = SAPClient()
            logger.info("🔧 Creando nuevo cliente SAP")
        
        # Verificar si la sesión es válida
        if not sap_client.is_session_valid():
            logger.info("🔄 Sesión SAP inválida, reconectando...")
            success = sap_client.login_from_env()
            if not success:
                logger.error("❌ Error al conectar a SAP")
                return None
            logger.info("✅ Sesión SAP restaurada")
        
        return sap_client
        
    except Exception as e:
        logger.error(f"❌ Error en get_sap_client: {e}")
        return None

# Crear servidor MCP
mcp_server = Server("sap-mcp-server")

# Crear aplicación FastAPI
app = FastAPI(
    title="SAP Business One MCP Server",
    description="Servidor MCP para conectar con SAP Business One Service Layer API",
    version="1.0.0"
)

@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Listar herramientas disponibles"""
    return [
        Tool(
            name="sap_connect",
            description="Conectar a SAP Business One",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="sap_status", 
            description="Verificar estado de conexión SAP",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="sap_create_sales_order",
            description="Crear una nueva Sales Order en SAP Business One",
            inputSchema={
                "type": "object",
                "properties": {
                    "CardCode": {
                        "type": "string",
                        "description": "Código del cliente (Business Partner)"
                    },
                    "DocDueDate": {
                        "type": "string",
                        "description": "Fecha de vencimiento (formato YYYYMMDD)"
                    },
                    "DocCurrency": {
                        "type": "string",
                        "description": "Moneda del documento (ej: USD, EUR)"
                    },
                    "DocRate": {
                        "type": "number",
                        "description": "Tasa de cambio"
                    },
                    "DocumentLines": {
                        "type": "array",
                        "description": "Líneas de productos/servicios",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ItemCode": {
                                    "type": "string",
                                    "description": "Código del artículo"
                                },
                                "Quantity": {
                                    "type": "string",
                                    "description": "Cantidad"
                                },
                                "TaxCode": {
                                    "type": "string",
                                    "description": "Código de impuesto (opcional)"
                                },
                                "UnitPrice": {
                                    "type": "string",
                                    "description": "Precio unitario"
                                }
                            },
                            "required": ["ItemCode", "Quantity"]
                        }
                    }
                },
                "required": ["CardCode", "DocumentLines"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Ejecutar herramientas"""
    global sap_client
    
    if name == "sap_connect":
        try:
            client = get_sap_client()
            if client:
                return [TextContent(
                    type="text",
                    text=f"✅ Conectado a SAP\nEmpresa: {client.company_db}\nSesión: {client.session_id[:20]}..."
                )]
            else:
                return [TextContent(
                    type="text",
                    text="❌ Error al conectar a SAP"
                )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error: {str(e)}"
            )]
    
    elif name == "sap_status":
        if sap_client and sap_client.session_id:
            return [TextContent(
                type="text",
                text=f"✅ Conectado\nEmpresa: {sap_client.company_db}\nSesión: {sap_client.session_id[:20]}..."
            )]
        else:
            return [TextContent(
                type="text",
                text="❌ Desconectado"
            )]
    
    elif name == "sap_create_sales_order":
        try:
            client = get_sap_client()
            if not client:
                return [TextContent(
                    type="text",
                    text="❌ No se pudo conectar a SAP"
                )]
            
            if not arguments:
                return [TextContent(
                    type="text",
                    text="❌ Faltan argumentos para crear Sales Order"
                )]
            
            # Validar argumentos requeridos
            if "CardCode" not in arguments:
                return [TextContent(
                    type="text",
                    text="❌ CardCode es requerido"
                )]
            
            if "DocumentLines" not in arguments or not arguments["DocumentLines"]:
                return [TextContent(
                    type="text",
                    text="❌ DocumentLines es requerido y no puede estar vacío"
                )]
            
            # Crear la Sales Order
            result = client.create_sales_order(arguments)
            
            # Extraer información esencial para respuesta limpia
            if isinstance(result, dict) and "DocEntry" in result:
                summary = {
                    "status": "success",
                    "message": "Sales Order creada exitosamente",
                    "DocEntry": result.get("DocEntry"),
                    "DocNum": result.get("DocNum"),
                    "CardCode": result.get("CardCode"),
                    "CardName": result.get("CardName"),
                    "DocDate": result.get("DocDate"),
                    "DocDueDate": result.get("DocDueDate"),
                    "DocTotal": result.get("DocTotal"),
                    "DocCurrency": result.get("DocCurrency"),
                    "DocRate": result.get("DocRate"),
                    "DocumentStatus": result.get("DocumentStatus")
                }
                
                return [TextContent(
                    type="text",
                    text=f"✅ Sales Order creada exitosamente:\n{json.dumps(summary, indent=2, ensure_ascii=False)}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"✅ Sales Order creada exitosamente:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
                )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error creando Sales Order: {str(e)}"
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"❌ Herramienta desconocida: {name}"
        )]

@app.post("/mcp")
async def handle_mcp_request(request: dict, response: Response):
    """Endpoint principal para manejar solicitudes MCP"""
    
    # Agregar header requerido para Microsoft Copilot Studio
    response.headers["x-ms-agentic-protocol"] = "mcp-streamable-1.0"
    
    try:
        logger.info(f"Recibida solicitud MCP: {request}")
        
        method = request.get("method")
        
        if method == "tools/list":
            tools = await handle_list_tools()
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {"tools": [tool.model_dump() for tool in tools]}
            }
            
        elif method == "tools/call":
            params = request.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments")
            
            result = await handle_call_tool(name, arguments)
            
            return {
                "jsonrpc": "2.0", 
                "id": request.get("id"),
                "result": {"content": [content.model_dump() for content in result]}
            }
            
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32601, "message": f"Método no encontrado: {method}"}
            }
            
    except Exception as e:
        logger.error(f"Error procesando solicitud MCP: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", None),
            "error": {"code": -32603, "message": f"Error interno: {str(e)}"}
        }

@app.get("/")
async def root():
    """Endpoint de información del servidor"""
    return {
        "name": "SAP Business One MCP Server",
        "version": "1.0.0",
        "description": "Servidor MCP para conectar con SAP Business One Service Layer API",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health"
        }
    }

@app.get("/health")
async def health():
    """Endpoint de salud del servidor"""
    global sap_client
    
    sap_status = "disconnected"
    if sap_client and sap_client.session_id:
        sap_status = "connected"
    
    return {
        "status": "healthy",
        "sap_connection": sap_status,
        "timestamp": "2025-08-20T00:00:00Z"
    }

if __name__ == "__main__":
    logger.info("🚀 Iniciando servidor MCP HTTP para SAP...")
    logger.info("Variables de entorno cargadas:")
    logger.info(f"  SAP_BASE_URL: {os.getenv('SAP_BASE_URL', 'No configurada')}")
    logger.info(f"  SAP_COMPANY_DB: {os.getenv('SAP_COMPANY_DB', 'No configurada')}")
    logger.info(f"  SAP_USERNAME: {os.getenv('SAP_USERNAME', 'No configurado')}")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
