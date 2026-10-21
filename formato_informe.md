# Formato del informe de revisión

Toda revisión de una legalización se entrega con este formato, sin texto antes ni después.

```
# Revisión de legalización <legalización>

- **Empleado:** <empleado>
- **Destino:** <ciudad> (Grupo <A o B>)
- **Viaje:** <salida> a <regreso>
- **Política aplicada:** viáticos, versión 2.0

| Id | Fecha | Categoría | Valor | Veredicto | Motivo |
|---|---|---|---|---|---|
| <una fila por gasto, en el orden del archivo> |

- **Gastos presentados:** <cantidad>
- **Aprobados:** <cantidad>
- **Rechazados:** <cantidad>
- **Devueltos:** <cantidad>

**Total a reembolsar: <suma de los aprobados>**
```

## Veredictos

- **Aprobado:** el gasto cumple la política. Se reconoce el valor completo.
- **Rechazado:** el gasto incumple la política. No se reconoce ningún valor. Un gasto que supera un tope se rechaza completo (política, sección 4).
- **Devuelto:** el gasto no se puede evaluar porque falta un dato o el dato no es válido. No se reconoce ningún valor hasta que el empleado lo corrija.

## Reglas del informe

- Un valor igual al tope está dentro del tope.
- Los gastos de hasta $30.000 COP no necesitan factura (política, sección 5).
- Los valores se escriben así: `$320.000 COP`.
- La columna **Motivo** cita la sección de la política. Queda vacía si el gasto se aprueba.
- El **Total a reembolsar** es la suma de los gastos aprobados.
