
import os

file_path = os.path.join('static', 'js', 'admin-panel.js')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Handle exception in handleSubirTema
old_catch_subir = "    } catch (error) {\n        mostrarResultado('Error de conexión al subir archivo', true);\n    }"
new_catch_subir = "    } catch (error) {\n        console.error('Error subiendo tema:', error);\n        mostrarResultado('Error de conexión al subir archivo', true);\n    }"
content = content.replace(old_catch_subir, new_catch_subir)

# Fix 2: Handle exception in handleSeleccionarTema
old_catch_seleccionar = "    } catch (error) {\n        mostrarResultado('Error de conexión al seleccionar tema', true);\n    }"
new_catch_seleccionar = "    } catch (error) {\n        console.error('Error seleccionando tema:', error);\n        mostrarResultado('Error de conexión al seleccionar tema', true);\n    }"
content = content.replace(old_catch_seleccionar, new_catch_seleccionar)

# Fix 3: Optional chaining
old_condition = "    if (!link || !link.href) return;"
new_condition = "    if (!link?.href) return;"
content = content.replace(old_condition, new_condition)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully refactored {file_path}")
