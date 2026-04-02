from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Configuración de conexión a la base de datos
DB_HOST = "localhost"
DB_NAME = "gestor_tareas"
DB_USER = "postgres" 
DB_PASS = "123" 

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

# 1. CREATE: Agregar una nueva tarea (POST)
@app.route('/tareas', methods=['POST'])
def crear_tarea():
    try:
        datos = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'INSERT INTO tareas (titulo, descripcion, estado) VALUES (%s, %s, %s) RETURNING id'
        cursor.execute(query, (datos['titulo'], datos['descripcion'], datos['estado']))
        
        # Obtenemos el ID de la tarea recién creada
        nuevo_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"mensaje": "Tarea creada exitosamente", "id": nuevo_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# 1.5 CREATE MASIVO: Agregar múltiples tareas a la vez (POST)
@app.route('/tareas/masivo', methods=['POST'])
def crear_tareas_masivas():
    try:
        # Recibimos una lista de diccionarios
        datos = request.get_json() 
        
        # Validamos que efectivamente sea una lista
        if not isinstance(datos, list):
            return jsonify({"error": "Se esperaba una lista de tareas [{}, {}, ...]"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Preparamos el query para una inserción estándar
        query = 'INSERT INTO tareas (titulo, descripcion, estado) VALUES (%s, %s, %s)'
        
        # Convertimos la lista de diccionarios en una lista de tuplas para psycopg2
        valores = [(d['titulo'], d['descripcion'], d['estado']) for d in datos]
        
        # executemany inserta todo el bloque de una sola vez, es mucho más rápido
        cursor.executemany(query, valores)
        conn.commit()
        
        # Obtenemos la cantidad de filas que se insertaron
        filas_insertadas = cursor.rowcount
        
        cursor.close()
        conn.close()
        return jsonify({"mensaje": f"Prueba de rendimiento exitosa: {filas_insertadas} tareas registradas"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. READ: Consultar todas las tareas (GET)
@app.route('/tareas', methods=['GET'])
def obtener_tareas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM tareas ORDER BY id ASC;')
        tareas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return jsonify(tareas), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. UPDATE: Actualizar una tarea existente (PUT)
@app.route('/tareas/<int:id>', methods=['PUT'])
def actualizar_tarea(id):
    try:
        datos = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'UPDATE tareas SET titulo = %s, descripcion = %s, estado = %s WHERE id = %s'
        cursor.execute(query, (datos['titulo'], datos['descripcion'], datos['estado'], id))
        
        # Verificamos si se actualizó alguna fila
        if cursor.rowcount == 0:
            return jsonify({"error": "Tarea no encontrada"}), 404
            
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"mensaje": "Tarea actualizada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. DELETE: Eliminar una tarea (DELETE)
@app.route('/tareas/<int:id>', methods=['DELETE'])
def eliminar_tarea(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'DELETE FROM tareas WHERE id = %s'
        cursor.execute(query, (id,))
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Tarea no encontrada"}), 404
            
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"mensaje": "Tarea eliminada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)