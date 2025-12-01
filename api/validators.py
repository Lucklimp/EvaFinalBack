from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
import re

# Validar que sea mayor o igual a cero
def validar_positivo(value):
    if value < 0:
        raise ValidationError('Este valor no puede ser negativo.')

# Validar RUT Chileno (Algoritmo Módulo 11)
def validar_rut_chileno(rut_raw):
    if not rut_raw:
        return

    # 1. Limpiar formato (quitar puntos y guión)
    rut = str(rut_raw).replace('.', '').replace('-', '').upper().strip()
    
    # 2. Validaciones básicas
    if len(rut) < 7:
        raise ValidationError("El RUT es demasiado corto.")
    
    # Separar cuerpo y dígito verificador (DV)
    cuerpo = rut[:-1]
    dv = rut[-1]

    # Validar que el cuerpo sean números
    if not cuerpo.isdigit():
        raise ValidationError("El cuerpo del RUT debe contener solo números.")

    # 3. Calcular Dígito Verificador esperado
    suma = 0
    multiplo = 2
    
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo += 1
        if multiplo == 8:
            multiplo = 2
            
    resto = suma % 11
    resultado = 11 - resto
    
    if resultado == 11:
        dv_calculado = '0'
    elif resultado == 10:
        dv_calculado = 'K'
    else:
        dv_calculado = str(resultado)

    # 4. Comparar
    if dv != dv_calculado:
        raise ValidationError("RUT inválido (Dígito verificador no coincide).")

# Validar Fechas (No futuras)
def validar_fecha_pasada(fecha):
    if fecha > timezone.now().date():
        raise ValidationError("La fecha no puede estar en el futuro.")