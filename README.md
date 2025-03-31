# <img width="62" alt="vilt" src="https://github.com/user-attachments/assets/010d608f-830b-4aeb-9a60-c96ca7cc89e8" /> Tutor Inteligente Virtual </br>

ViLT es un marco de desarrollo completo que integra un chatbot inteligente. Está diseñado para asistir mediante tutorías virtuales a los estudiantes en las asignaturas de las diferentes titulaciones de la ETSII en la URJC. Utiliza diversos modelos extensos de lenguaje para el procesamiento del lenguaje natural junto a LangChain y técnicas RAG para optimizar las consultas al modelo de lenguaje. ViLT permite a los profesores subir material en PDF y gestionar la incorporación de profesores y estudiantes a las asignaturas, todo mientras recoge feedback para mejorar continuamente.

URL: `https://dolguldur.etsii.urjc.es`

## Requisitos

Antes de ejecutar la aplicación, asegúrate de que tu entorno cumple con los siguientes requisitos:

- Python 3.7 o superior.
- Acceso a Internet para cargar el modelo de lenguaje.
- Entorno para la base de datos MONGODB.
- Entorno para el OLLAMA / API_KEY para OpenAI

## Instalación local

1. Clona este repositorio en tu máquina local:

   ```bash
   git clone https://github.com/URJCDSLab/ViLT.git
   ```

2. Ve al directorio del proyecto:

   ```bash
   cd ViLT
   ```

3. Instala las dependencias de Python utilizando pip:

   ```bash
   pip install -r requirements.txt
   ```

## Ejecución local

Una vez que hayas configurado todo, puedes iniciar la aplicación ejecutando el servidor de desarrollo en el fichero `main.py`:

### Flujo de Trabajo

1. **Carga de Conocimiento**: Los profesores suben material en PDF a través de la interfaz de usuario. Este material se procesa y se indexa utilizando ChromaDB, preparándolo para consultas rápidas.
   
2. **Consulta de Conocimiento**: Cuando un alumno realiza una consulta, se recibe la solicitud y la procesa utilizando Llama 3.1 o un modelo OpenAI (modificable según configuración) + LangChain para extraer la respuesta más relevante.
   
3. **Respuesta y Feedback**: ViLT entrega la respuesta al estudiante. Además, recoge feedback para ajustar y mejorar continuamente la precisión y relevancia de las respuestas.





