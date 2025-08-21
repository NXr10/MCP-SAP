

import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import urllib3
import os

# Desactivar advertencias SSL para desarrollo local
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SAPClient:

    
    def __init__(self, base_url: Optional[str] = None):
    
        
        # Obtener URL desde variable de entorno si no se proporciona
        if base_url is None:
            base_url = os.getenv('SAP_BASE_URL')
        
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.session_timeout: Optional[datetime] = None
        self.session = requests.Session()
        
        # Configurar session para HTTPS sin verificación (solo desarrollo local)
        self.session.verify = False
        
        # Headers por defecto
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"SAP Client inicializado para {base_url}")
    
    def login_from_env(self) -> bool:
       

        
        # Obtener credenciales desde variables de entorno
        company_db = os.getenv('SAP_COMPANY_DB')
        username = os.getenv('SAP_USERNAME')
        password = os.getenv('SAP_PASSWORD')
        
        # Validar que todas las credenciales estén disponibles
        missing_vars = []
        if not company_db:
            missing_vars.append('SAP_COMPANY_DB')
        if not username:
            missing_vars.append('SAP_USERNAME')
        if not password:
            missing_vars.append('SAP_PASSWORD')
        
        if missing_vars:
            logger.error(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
            return False
        
        # Realizar login con credenciales obtenidas
        return self.login(company_db, username, password)

    def login(self, company_db: str, username: str, password: str) -> bool:
        """Realizar login a SAP Business One Service Layer"""
        if not self.base_url:
            logger.error("URL base no configurada")
            return False
            
        login_url = f"{self.base_url}/Login"
        
        # Payload según la especificación de SAP Service Layer API
        payload = {
            "CompanyDB": company_db,
            "Password": password,
            "UserName": username
        }
        
        try:
            logger.info(f"Intentando login a SAP: {login_url}")
            logger.info(f"Company DB: {company_db}, Username: {username}")
            
            response = self.session.post(login_url, json=payload)
            
            logger.info(f"Respuesta del login: Status {response.status_code}")
            
            if response.status_code == 200:
                # Obtener session ID del response body
                response_data = response.json()
                self.session_id = response_data.get('SessionId')
                self.company_db = company_db  # Guardar company_db como atributo
                
                # Obtener cookies B1SESSION y ROUTEID
                b1session = response.cookies.get('B1SESSION')
                routeid = response.cookies.get('ROUTEID')
                
                if self.session_id:
                    logger.info(f"Login exitoso. Session ID: {self.session_id}")
                    
                    # Agregar B1SESSION cookie a headers para futuras requests
                    if b1session:
                        self.session.cookies.set('B1SESSION', b1session)
                        logger.info("Cookie B1SESSION configurada")
                    
                    if routeid:
                        self.session.cookies.set('ROUTEID', routeid)
                        logger.info("Cookie ROUTEID configurada")
                    
                    # Configurar timeout de sesión
                    # Por defecto SAP usa 30 minutos, pero puede ser configurado en b1s.conf
                    session_timeout = response_data.get('SessionTimeout', 30)
                    self.session_timeout = datetime.now() + timedelta(minutes=session_timeout)
                    
                    logger.info(f"Sesión configurada - Timeout: {session_timeout} minutos")
                    logger.info(f"Sesión expira: {self.session_timeout}")
                    
                    return True
                else:
                    logger.error("Login falló: No se recibió Session ID")
                    return False
            else:
                logger.error(f"Login falló: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error durante login: {e}")
            return False
            logger.info(f"Intentando login en SAP para usuario: {username}")
            
            response = self.session.post(login_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                # SAP devuelve el SessionId en las cookies
                session_cookie = response.cookies.get('B1SESSION')
                if session_cookie:
                    self.session_id = session_cookie
                    # Establecer timeout de sesión (SAP típicamente 30 minutos)
                    self.session_timeout = datetime.now() + timedelta(minutes=30)
                    
                    # Agregar cookie a futuras peticiones
                    self.session.cookies.set('B1SESSION', session_cookie)
                    
                    logger.info("Login exitoso en SAP")
                    return True
                else:
                    logger.error("Login exitoso pero no se recibió SessionId")
                    return False
            else:
                logger.error(f"Error en login SAP: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión al hacer login: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en login: {str(e)}")
            return False
    
    def is_session_valid(self) -> bool:
        """
        Verifica si la sesión actual es válida
        
        Returns:
            bool: True si la sesión es válida, False en caso contrario
        """
        if not self.session_id or not self.session_timeout:
            return False
        
        # Verificar si la sesión no ha expirado
        if datetime.now() >= self.session_timeout:
            logger.info("Sesión SAP expirada")
            return False
        
        return True
    
    def logout(self) -> bool:
        """
        Cierra la sesión en SAP usando POST según documentación oficial
        
        Por defecto, una sesión expira automáticamente después de 30 minutos
        de inactividad. Este método hace logout explícito.
        
        Returns:
            bool: True si logout exitoso
        """
        if not self.session_id:
            logger.info("No hay sesión activa para hacer logout")
            return True
        
        try:
            logout_url = f"{self.base_url}/Logout"
            logger.info(f"Haciendo logout: {logout_url}")
            
            # POST al endpoint de Logout según documentación SAP
            response = self.session.post(logout_url, timeout=10)
            
            logger.info(f"Logout response: {response.status_code}")
            
            # SAP puede devolver diferentes códigos según la implementación
            if response.status_code in [200, 204]:
                logger.info("Logout exitoso de SAP")
            elif response.status_code == 401:
                logger.info("Sesión ya expirada (logout implícito)")
            else:
                logger.warning(f"Logout con código inesperado: {response.status_code}")
                # Mostrar respuesta para debugging
                if response.text:
                    logger.warning(f"Respuesta logout: {response.text[:200]}")
            
            # Limpiar sesión local independientemente del resultado
            self.session_id = None
            self.session_timeout = None
            self.session.cookies.clear()
            
            logger.info("Sesión local limpiada")
            return True
            
        except Exception as e:
            logger.error(f"Error en logout: {str(e)}")
            # Limpiar sesión local aunque haya error de comunicación
            self.session_id = None
            self.session_timeout = None
            self.session.cookies.clear()
            logger.info("Sesión local limpiada por error")
            return False
            
        except Exception as e:
            logger.error(f"Error en logout: {str(e)}")
            # Limpiar sesión local aunque haya error
            self.session_id = None
            self.session_timeout = None
            self.session.cookies.clear()
            return False
    
    def make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None, json_data: dict = None) -> any:
        """
        Hacer una request al SAP Service Layer con autenticación
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE, etc.)
            endpoint: Endpoint de la API (ej: '/Items', '/BusinessPartners')
            data: Datos para POST/PUT (form data)
            params: Parámetros de query string
            json_data: Datos JSON para POST/PUT
            
        Returns:
            dict or requests.Response: Para GET devuelve dict, para POST devuelve dict o Response
            
        Raises:
            ValueError: Si no hay sesión válida
            requests.RequestException: Si hay error en la request
        """
        # Verificar sesión válida
        if not self.is_session_valid():
            raise ValueError("No hay sesión válida. Ejecutar login() primero.")
        
        # Construir URL completa
        url = f"{self.base_url}{endpoint}"
        
        # Headers para JSON
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            logger.info(f"SAP Request: {method} {url}")
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
                
            elif method.upper() == "POST":
                if json_data:
                    response = self.session.post(url, json=json_data, headers=headers)
                else:
                    response = self.session.post(url, data=data, params=params, headers=headers)
                
                response.raise_for_status()
                
                # SAP puede retornar 204 No Content en algunos casos
                if response.status_code == 204:
                    return {"status": "created", "message": "Document created successfully"}
                
                try:
                    return response.json()
                except:
                    return {"status": "created", "response": response.text}
                    
            else:
                # Para otros métodos HTTP
                if json_data:
                    response = self.session.request(method, url, json=json_data, headers=headers)
                else:
                    response = self.session.request(method, url, data=data, params=params, headers=headers)
                
                response.raise_for_status()
                
                if response.status_code == 204:
                    return {"status": "success"}
                
                try:
                    return response.json()
                except:
                    return {"status": "success", "response": response.text}
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en request SAP: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en request: {e}")
            raise
    def get_business_partners(self, filter_query: str = "", top: int = 10) -> dict:
        """
        Obtener Business Partners de SAP
        
        Args:
            filter_query: Filtro OData (ej: "CardCode eq 'C20000'")
            top: Número máximo de registros
            
        Returns:
            dict: Datos de Business Partners
        """
        endpoint = "/BusinessPartners"
        
        params = {}
        if filter_query:
            params['$filter'] = filter_query
        if top:
            params['$top'] = top
            
        return self.make_request("GET", endpoint, params=params)
    
    def get_items(self, filter_query: str = None, top: int = None) -> dict:
        """
        Obtener Items de SAP
        
        Args:
            filter_query: Filtro OData
            top: Número máximo de registros
            
        Returns:
            dict: Datos de Items
        """
        endpoint = "/Items"
        
        params = {}
        if filter_query:
            params['$filter'] = filter_query
        if top:
            params['$top'] = top
            
        return self.make_request("GET", endpoint, params=params)
    
    def get_sales_orders(self, filter_query: str = None, top: int = None) -> dict:
        """
        Obtener Sales Orders de SAP
        
        Args:
            filter_query: Filtro OData
            top: Número máximo de registros
            
        Returns:
            dict: Datos de Sales Orders
        """
        endpoint = "/Orders"
        
        params = {}
        if filter_query:
            params['$filter'] = filter_query
        if top:
            params['$top'] = top
            
        return self.make_request("GET", endpoint, params=params)

    def __del__(self):
     
        if self.session_id:
            self.logout()

    def create_sales_order(self, order_data: dict) -> dict:
        """
        Crear una Sales Order en SAP Business One
        
        Args:
            order_data (dict): Datos de la orden con estructura:
            {
                "CardCode": "C-00000001",
                "DocDueDate": "20250830", 
                "DocCurrency": "USD",
                "DocRate": 8.25,
                "DocumentLines": [
                    {
                        "ItemCode": "ACC-00025",
                        "Quantity": "100",
                        "TaxCode": "IVA",
                        "UnitPrice": "1000"
                    }
                ]
            }
            
        Returns:
            dict: Respuesta de SAP con la orden creada
            
        Raises:
            Exception: Si hay error en la creación
        """
        if not self.is_session_valid():
            raise Exception("Sesión SAP no válida. Debe hacer login primero.")
        
        endpoint = "/Orders"
        
        try:
            logger.info(f"Creando Sales Order para CardCode: {order_data.get('CardCode')}")
            logger.info(f"Líneas de documento: {len(order_data.get('DocumentLines', []))}")
            
            # Validar datos requeridos
            required_fields = ['CardCode', 'DocumentLines']
            for field in required_fields:
                if field not in order_data:
                    raise ValueError(f"Campo requerido faltante: {field}")
            
            if not order_data['DocumentLines']:
                raise ValueError("DocumentLines no puede estar vacío")
            
            # Validar líneas de documento
            for i, line in enumerate(order_data['DocumentLines']):
                required_line_fields = ['ItemCode', 'Quantity']
                for field in required_line_fields:
                    if field not in line:
                        raise ValueError(f"Campo requerido en línea {i+1}: {field}")
            
            # Realizar POST request
            response = self.make_request("POST", endpoint, json_data=order_data)
            
            if isinstance(response, dict):
                logger.info(f"Sales Order creada exitosamente. DocEntry: {response.get('DocEntry', 'N/A')}")
                return response
            else:
                raise Exception("Respuesta inesperada de SAP")
                
        except Exception as e:
            logger.error(f"Error creando Sales Order: {e}")
            raise


# Función auxiliar para crear cliente SAP desde variables de entorno
def create_sap_client_from_env() -> SAPClient:

 
    
    base_url = os.getenv('SAP_BASE_URL')
    return SAPClient(base_url)
