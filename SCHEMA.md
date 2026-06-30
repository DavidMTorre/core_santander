# Esquema de Base de Datos

> Base de datos PostgreSQL de una financiera/microfinanciera (Perú).
> Maneja clientes, créditos, cronograma de pagos, scoring transaccional, fichas de campo, cobranza y la app del cliente.
> Esquema: `public`. Todas las PK son `uuid` con `gen_random_uuid()` salvo que se indique lo contrario.
>
> **Última actualización:** se agregaron las tablas de **M6 — Cronograma de Pagos**: `cronograma_cuotas` y `pagos`. No se modificó ninguna tabla preexistente.

## Convenciones
- `PK` = Primary Key · `FK` = Foreign Key · `UQ` = Unique · `NN` = Not Null
- Tipos abreviados: `uuid`, `varchar` (character varying), `text`, `numeric`, `int`, `smallint`, `bool`, `date`, `time`, `timestamptz` (timestamp with time zone), `jsonb`.

---

## Mapa de relaciones (alto nivel)

```
agencias ──< asesores_negocio ──< clientes ──< creditos ──< cronograma_cuotas ──< pagos
   │              │                  │            │                                  │
   │              │                  │            └──< pagos ───────────────────────┘  (pagos también referencia credito_id y cliente_id)
   │              │                  │            │
   │              │                  ├──< solicitudes_credito ──< solicitudes_documentos
   │              │                  │                         └──< solicitudes_notas_internas
   │              │                  ├──< consultas_buro
   │              │                  ├──< creditos_preaprobados
   │              │                  ├──< campanas_activas
   │              │                  ├──< cartera_diaria ──< acciones_cobranza / alertas_cartera
   │              │                  ├──< cliente_app_auth / cliente_dispositivos
   │              │                  ├──< cliente_documentos / cliente_notificaciones / cliente_soporte
   │              │                  └──< (historial_credito)

cuentas ──< transacciones / movimientos_mensuales        (vinculadas por user_id)
scores_transaccionales ──< fichas_campo
oficiales ──< solicitudes ──< documentos
```

> Nota: las tablas con sufijo `*_clientes`, `features_scoring`, `scores_transaccionales`, `cuentas`, `transacciones`, `movimientos_mensuales` usan una columna `user_id` (uuid) que **no** tiene FK declarada hacia `clientes`; se relacionan por convención de aplicación. Tenerlo en cuenta al hacer joins.

---

## Tablas

### `agencias`
Catálogo de agencias/sucursales.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| nombre | varchar | NN | | |
| codigo | varchar | NN | | UQ |
| region | varchar | | | |
| departamento | varchar | | | |
| provincia | varchar | | | |
| distrito | varchar | | | |
| direccion | text | | | |
| lat | numeric | | | |
| lng | numeric | | | |
| jefe_agencia | varchar | | | |
| activa | bool | | true | |
| created_at | timestamptz | | now() | |

---

### `asesores_negocio`
Asesores de negocio / cobranza (usuarios operativos del back-office y app de campo).

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| user_id | uuid | | | UQ |
| codigo_empleado | varchar | NN | | UQ |
| nombres | varchar | NN | | |
| apellidos | varchar | NN | | |
| agencia_id | uuid | | | FK → agencias.id |
| perfil | varchar | NN | 'operador' | |
| nivel | varchar | | | |
| zona_asignada | text | | | |
| telefono | varchar | | | |
| token_fcm | text | | | push notifications |
| password_hash | text | | | hash bcrypt para login del panel (comité) |
| activo | bool | | true | |
| created_at | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

---

### `clientes`
Cliente / titular del negocio.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| numero_documento | varchar | NN | | UQ, indexado |
| tipo_documento | varchar | | 'DNI' | |
| nombres | varchar | NN | | |
| apellidos | varchar | NN | | |
| fecha_nacimiento | date | | | |
| estado_civil | varchar | | | |
| grado_instruccion | varchar | | | |
| telefono | varchar | | | |
| email | varchar | | | |
| direccion | text | | | |
| tipo_negocio | varchar | | | |
| nombre_negocio | varchar | | | |
| actividad_economica_ciiu | varchar | | | |
| antiguedad_negocio_meses | int | | 0 | |
| ingresos_estimados | numeric | | | |
| lat | numeric | | | |
| lng | numeric | | | |
| calificacion_sbs | varchar | | 'Normal' | |
| num_entidades_sbs | smallint | | 0 | |
| deuda_total_sbs | numeric | | 0 | |
| asesor_id | uuid | | | FK → asesores_negocio.id |
| agencia_id | uuid | | | FK → agencias.id |
| estado | varchar | | 'activo' | |
| en_lista_negra | bool | | false | |
| motivo_lista_negra | text | | | |
| created_at | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

---

### `creditos`
Créditos desembolsados / vigentes.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| cliente_id | uuid | NN | | FK → clientes.id |
| asesor_id | uuid | | | FK → asesores_negocio.id |
| agencia_id | uuid | | | FK → agencias.id |
| numero_credito | varchar | | | UQ |
| producto | varchar | | | |
| monto_desembolsado | numeric | NN | | |
| plazo_meses | int | NN | | |
| tea | numeric | | | tasa efectiva anual |
| tipo_cuota | varchar | | 'mensual' | |
| garantia | varchar | | 'sin_garantia' | |
| estado | varchar | | 'vigente' | |
| fecha_desembolso | date | | | |
| fecha_vencimiento | date | | | |
| saldo_actual | numeric | | | |
| cuotas_total | int | | | |
| cuotas_pagadas | int | | 0 | |
| dias_mora | int | | 0 | |
| monto_vencido | numeric | | 0 | |
| created_at | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

Índices: `idx_creditos_cliente (cliente_id, estado)`.

---

### `cronograma_cuotas`  🆕 M6
Plan de cuotas detallado por crédito (read-only para el cliente). Fuente del detalle del cronograma; `creditos` mantiene los agregados (`saldo_actual`, `cuotas_pagadas`, `monto_vencido`). Una fila por cuota.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| credito_id | uuid | NN | | FK → creditos.id (ON DELETE CASCADE) |
| cliente_id | uuid | NN | | FK → clientes.id (ON DELETE RESTRICT). Denormalizado para RLS/offline |
| numero_cuota | int | NN | | UQ con credito_id; > 0 |
| fecha_vencimiento | date | NN | | |
| monto_cuota | numeric(14,2) | NN | | total de la cuota |
| monto_capital | numeric(14,2) | NN | | |
| monto_interes | numeric(14,2) | NN | | |
| monto_mora | numeric(14,2) | NN | 0 | |
| otros_cargos | numeric(14,2) | NN | 0 | portes, seguros |
| saldo_capital | numeric(14,2) | | | saldo de capital posterior |
| estado | varchar(20) | NN | 'pendiente' | pendiente \| pagada \| parcial \| vencida |
| monto_pagado | numeric(14,2) | NN | 0 | acumulado abonado a la cuota |
| fecha_pago | date | | | fecha de cancelación total |
| dias_mora | int | NN | 0 | |
| notificada | bool | NN | false | notificación de vencimiento ya enviada (M5) |
| fecha_ultima_notificacion | timestamptz | | | |
| created_at | timestamptz | NN | now() | |
| updated_at | timestamptz | NN | now() | trigger set_updated_at() |

UQ: `(credito_id, numero_cuota)`.
CHECK: `numero_cuota > 0`; montos `>= 0`; `dias_mora >= 0`; `estado IN (...)`.
Índices: `idx_cronograma_cliente (cliente_id)`, `idx_cronograma_credito_estado (credito_id, estado)`, `idx_cronograma_vencimiento (fecha_vencimiento)`, `idx_cronograma_estado_vencimiento (estado, fecha_vencimiento)`.
RLS: lectura del cliente dueño (`cliente_id = current_cliente_id()`) y del asesor de la cartera; escritura solo `service_role`.

---

### `pagos`  🆕 M6
Historial de pagos aplicados a un crédito (read-only para el cliente). Un pago puede aplicar a una cuota (`cuota_id`) o ser adelanto/prepago no atado a una sola cuota (`cuota_id` NULL).

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| credito_id | uuid | NN | | FK → creditos.id (ON DELETE RESTRICT) |
| cliente_id | uuid | NN | | FK → clientes.id (ON DELETE RESTRICT). Denormalizado para RLS/offline |
| cuota_id | uuid | | | FK → cronograma_cuotas.id (ON DELETE SET NULL) |
| numero_cuota | int | | | denormalizado opcional (UI) |
| monto_pagado | numeric(14,2) | NN | | total del pago; > 0 |
| monto_capital | numeric(14,2) | NN | 0 | desglose opcional |
| monto_interes | numeric(14,2) | NN | 0 | desglose opcional |
| monto_mora | numeric(14,2) | NN | 0 | desglose opcional |
| fecha_pago | timestamptz | NN | now() | |
| medio_pago | varchar(40) | | | efectivo \| transferencia \| app \| agente |
| canal | varchar(40) | | | |
| referencia_externa | varchar(80) | | | id del core/gateway; UQ parcial (idempotencia) |
| estado | varchar(20) | NN | 'confirmado' | confirmado \| anulado \| pendiente |
| observaciones | text | | | |
| created_at | timestamptz | NN | now() | |
| updated_at | timestamptz | NN | now() | trigger set_updated_at() |

CHECK: `monto_pagado > 0`; desgloses `>= 0`; `estado IN (...)`.
Índices: `idx_pagos_credito_fecha (credito_id, fecha_pago DESC)`, `idx_pagos_cliente (cliente_id)`, `idx_pagos_cuota (cuota_id)`, `uq_pagos_referencia_externa` (UNIQUE parcial WHERE `referencia_externa IS NOT NULL`).
RLS: lectura del cliente dueño y del asesor de la cartera; escritura solo `service_role`.

---

### `creditos_preaprobados`
Ofertas de crédito pre-aprobadas por cliente.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| cliente_id | uuid | NN | | FK → clientes.id |
| asesor_id | uuid | | | FK → asesores_negocio.id |
| monto_maximo | numeric | NN | | |
| plazo_sugerido_meses | int | | | |
| tea_referencial | numeric | | | |
| score_confianza | int | | 0 | |
| vigente | bool | | true | |
| fecha_calculo | date | | CURRENT_DATE | |
| fecha_vencimiento | date | | | |
| score_transaccional | smallint | | 0 | |
| segmento | varchar | | 'NO_APLICA' | |
| ingreso_promedio_ref | numeric | | | |
| created_at | timestamptz | | now() | |

Índices: `idx_preaprobados_cliente (cliente_id, vigente)`.

---

### `solicitudes_credito`
Expediente/solicitud de crédito (flujo multi-paso del asesor).

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| numero_expediente | varchar | | | UQ |
| asesor_id | uuid | NN | | FK → asesores_negocio.id |
| cliente_id | uuid | | | FK → clientes.id |
| agencia_id | uuid | | | FK → agencias.id |
| tipo_negocio | varchar | | | |
| nombre_negocio | varchar | | | |
| actividad_economica | varchar | | | |
| antiguedad_negocio_meses | int | | | |
| ingresos_estimados | numeric | | | |
| gastos_mensuales | numeric | | | |
| patrimonio_estimado | numeric | | | |
| tiene_conyuge | bool | | false | |
| conyuge_json | jsonb | | | |
| tiene_garante | bool | | false | |
| garante_json | jsonb | | | |
| monto_solicitado | numeric | NN | | |
| plazo_meses | int | NN | | |
| moneda | varchar | | 'PEN' | |
| tipo_cuota | varchar | | 'mensual' | |
| garantia | varchar | | 'sin_garantia' | |
| destino_credito | text | | | |
| cuota_estimada | numeric | | | |
| tea_referencial | numeric | | | |
| estado | varchar | | 'borrador' | |
| paso_actual | smallint | | 1 | |
| monto_aprobado | numeric | | | |
| motivo_rechazo | text | | | |
| condicion_adicional | text | | | |
| analista_asignado | varchar | | | |
| firma_cliente_base64 | text | | | |
| lat_captura | numeric | | | |
| lng_captura | numeric | | | |
| pendiente_sync | bool | | false | offline-first |
| canal | varchar(20) | NN | 'cliente' | origen de la solicitud |
| created_at | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

Índices: `idx_solicitudes_asesor (asesor_id, estado)`, `idx_solicitudes_cliente (cliente_id)`.
CHECK: `canal IN ('cliente','asesor')`.

---

### `solicitudes_documentos`
Documentos adjuntos a una `solicitudes_credito`.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| solicitud_id | uuid | NN | | FK → solicitudes_credito.id |
| tipo_documento | varchar | NN | | |
| storage_url | text | NN | | |
| tamanio_kb | int | | | |
| nitidez_score | numeric | | | calidad de imagen |
| es_obligatorio | bool | | true | |
| created_at | timestamptz | | now() | |

---

### `solicitudes_notas_internas`
Notas internas del asesor sobre una solicitud.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| solicitud_id | uuid | NN | | FK → solicitudes_credito.id |
| asesor_id | uuid | NN | | FK → asesores_negocio.id |
| contenido | text | NN | | |
| created_at | timestamptz | | now() | |

---

### `consultas_buro`
Consultas a buró / SBS con consentimiento firmado. Soporta reutilización de consultas previas.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| asesor_id | uuid | NN | | FK → asesores_negocio.id |
| cliente_id | uuid | NN | | FK → clientes.id |
| solicitud_id | uuid | | | FK → solicitudes_credito.id |
| dni_consultado | varchar | NN | | |
| calificacion_sbs | varchar | | | |
| entidades_con_deuda | int | | 0 | |
| deuda_total_pen | numeric | | 0 | |
| mayor_deuda | numeric | | 0 | |
| dias_mayor_mora | int | | 0 | |
| resultado_json | jsonb | | | |
| firma_consentimiento_base64 | text | | | |
| timestamp_consentimiento | timestamptz | | | |
| reutilizada | bool | | false | |
| consulta_original_id | uuid | | | FK → consultas_buro.id (auto-ref) |
| created_at | timestamptz | | now() | |

Índices: `idx_buro_cliente (cliente_id, created_at DESC)`.

---

### `cartera_diaria`
Cartera asignada por día al asesor para gestión/visita (cobranza y comercial).

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| asesor_id | uuid | NN | | FK → asesores_negocio.id |
| cliente_id | uuid | NN | | FK → clientes.id |
| agencia_id | uuid | | | FK → agencias.id |
| credito_id | uuid | | | FK → creditos.id |
| fecha_asignacion | date | NN | CURRENT_DATE | |
| tipo_gestion | varchar | NN | | |
| prioridad | varchar | | 'NORMAL' | |
| score_prioridad | int | | 0 | |
| estado_visita | varchar | | 'pendiente' | |
| resultado_visita | varchar | | | |
| observacion_visita | text | | | |
| timestamp_visita | timestamptz | | | |
| lat_visita | numeric | | | |
| lng_visita | numeric | | | |
| orden_manual | int | | | |
| created_at | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

Índices: `idx_cartera_estado (estado_visita)`, `idx_cartera_asesor_fecha (asesor_id, fecha_asignacion)`.
UQ: `(asesor_id, cliente_id, fecha_asignacion)`.

---

### `acciones_cobranza`
Gestiones de cobranza realizadas (con geolocalización y compromisos de pago).

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| asesor_id | uuid | NN | | FK → asesores_negocio.id |
| cliente_id | uuid | NN | | FK → clientes.id |
| credito_id | uuid | | | FK → creditos.id |
| tipo_gestion | varchar | NN | | |
| resultado | varchar | NN | | |
| monto_pagado | numeric | | | |
| fecha_compromiso | date | | | |
| monto_compromiso | numeric | | | |
| observaciones | text | | | |
| lat | numeric | | | |
| lng | numeric | | | |
| timestamp_gestion | timestamptz | | now() | |

---

### `alertas_cartera`
Alertas para el asesor sobre su cartera.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| asesor_id | uuid | NN | | FK → asesores_negocio.id |
| cliente_id | uuid | | | FK → clientes.id |
| credito_id | uuid | | | FK → creditos.id |
| tipo_alerta | varchar | NN | | |
| mensaje | text | | | |
| leida | bool | | false | |
| created_at | timestamptz | | now() | |

Índices: `idx_alertas_asesor_leida (asesor_id, leida)`.

---

### `campanas_activas`
Campañas comerciales activas asignadas a cliente/asesor.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| asesor_id | uuid | | | FK → asesores_negocio.id |
| cliente_id | uuid | | | FK → clientes.id |
| tipo | varchar | NN | | |
| monto_ofertado | numeric | | | |
| fecha_vencimiento | date | | | |
| activa | bool | | true | |
| gestionada | bool | | false | |
| fecha_gestion | timestamptz | | | |
| created_at | timestamptz | | now() | |

---

### `fichas_campo`
Ficha de evaluación de campo (visita) con scoring por componentes. Vinculada por `user_id` y a `scores_transaccionales`.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| user_id | uuid | NN | | (cliente, sin FK declarada) |
| score_id | uuid | | | FK → scores_transaccionales.id |
| asesor_nombre | text | NN | | |
| agencia | text | NN | | |
| fecha_visita | date | NN | | |
| hora_inicio | time | | | |
| hora_fin | time | | | |
| negocio_verificado | bool | NN | false | |
| motivo_no_verificado | text | | | |
| antiguedad_negocio | text | | | |
| pts_antiguedad | smallint | | 0 | |
| tenencia_local | text | | | |
| pts_tenencia | smallint | | 0 | |
| direccion_verificada | text | | | |
| pts_f1 | smallint | | 0 | factor 1 |
| ventas_diarias_rango | text | | | |
| pts_ventas | smallint | | 0 | |
| ventas_mensuales_est | numeric | | | |
| gastos_fijos_mes | numeric | | | |
| ratio_gastos | text | | | |
| pts_gastos | smallint | | 0 | |
| ingreso_consistente | bool | | true | |
| obs_inconsistencia | text | | | |
| pts_f2 | smallint | | 0 | factor 2 |
| tiene_deuda_informal | text | | | |
| pts_deuda_informal | smallint | | 0 | |
| monto_deuda_informal | numeric | | 0 | |
| detalle_deuda | text | | | |
| participa_pandero | text | | | |
| pts_pandero | smallint | | 0 | |
| aporte_pandero_mes | numeric | | 0 | |
| pts_f3 | smallint | | 0 | factor 3 |
| stock_visible | text | | | |
| pts_stock | smallint | | 0 | |
| activos_hogar | text | | | |
| pts_activos | smallint | | 0 | |
| descripcion_activos | text | | | |
| pts_f4 | smallint | | 0 | factor 4 |
| caracter_resultado | text | NN | 'sin_penalidad' | |
| obs_caracter | text | | | |
| score_campo | smallint | | 0 | |
| score_transaccional_ref | smallint | | 0 | |
| score_final | smallint | | 0 | |
| segmento_resultante | text | | 'NO_APLICA' | |
| monto_aprobado_propuesto | numeric | | | |
| plazo_propuesto_meses | smallint | | | |
| cuota_estimada | numeric | | | |
| recomendacion_asesor | text | | | |
| obs_finales | text | | | |
| comite_resolucion | text | | | |
| comite_monto_final | numeric | | | |
| comite_plazo_final | smallint | | | |
| comite_motivo_rechazo | text | | | |
| jefe_agencia | text | | | |
| fecha_comite | date | | | |
| estado_ficha | text | | 'en_proceso' | |
| created_at | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

---

### `scores_transaccionales`
Score transaccional calculado por componentes. Una fila por `user_id`.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| user_id | uuid | NN | | UQ (cliente, sin FK declarada) |
| pts_saldo | smallint | | 0 | |
| pts_regularidad | smallint | | 0 | |
| pts_disciplina | smallint | | 0 | |
| pts_vinculo | smallint | | 0 | |
| pts_riesgo | smallint | | 0 | |
| score_transaccional | smallint | | 0 | |
| segmento_preliminar | text | | 'NO_APLICA' | |
| monto_hipotesis | numeric | | 0 | |
| ingreso_promedio_ref | numeric | | 0 | |
| cuota_max_ref | numeric | | 0 | |
| es_valido | bool | | true | |
| motivo_invalido | text | | | |
| fecha_calculo | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

---

### `features_scoring`
Features pre-calculadas para el scoring. Una fila por `user_id`.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| user_id | uuid | NN | | UQ |
| saldo_promedio | numeric | | 0 | |
| saldo_minimo | numeric | | 0 | |
| meses_saldo_positivo | smallint | | 0 | |
| ingreso_promedio | numeric | | 0 | |
| meses_con_abono | smallint | | 0 | |
| volatilidad_ingresos | numeric | | 0 | |
| ratio_ahorro_neto | numeric | | 0 | |
| depositos_recurrentes | smallint | | 0 | |
| antiguedad_cuenta_meses | int | | 0 | |
| meses_activos | smallint | | 0 | |
| edad | smallint | | 0 | |
| num_entidades_sbs | smallint | | 0 | |
| cuota_max_estimada | numeric | | 0 | |
| monto_max_por_ingreso | numeric | | 0 | |
| periodos_analizados | smallint | | 0 | |
| fecha_calculo | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

---

### `perfiles_clientes`
Perfil extendido del cliente (datos de negocio y SBS). Una fila por `user_id`.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| user_id | uuid | NN | | UQ |
| dni | text | | | |
| nombres | text | | | |
| apellidos | text | | | |
| fecha_nacimiento | date | | | |
| edad | int | | | |
| telefono | text | | | |
| distrito | text | | | |
| provincia | text | | | |
| departamento | text | | | |
| nombre_negocio | text | | | |
| tipo_negocio | text | | | |
| direccion_negocio | text | | | |
| lat_negocio | numeric | | | |
| lng_negocio | numeric | | | |
| antiguedad_negocio_meses | int | | 0 | |
| tenencia_local | text | | | |
| num_entidades_sbs | smallint | | 0 | |
| calificacion_sbs | text | | 'Normal' | |
| deuda_total_sbs | numeric | | 0 | |
| estado_cliente | text | | 'activo' | |
| created_at | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

---

### `cuentas`
Cuentas bancarias del cliente (insumo del scoring transaccional).

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| user_id | uuid | | | |
| tipo | text | | 'ahorros' | |
| saldo | numeric | | 0 | |
| moneda | text | | 'PEN' | |
| numero_cuenta | text | | | |
| created_at | timestamptz | | now() | |

---

### `transacciones`
Transacciones de cuenta.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| user_id | uuid | | | |
| cuenta_id | uuid | | | FK → cuentas.id |
| tipo | text | | | |
| monto | numeric | | | |
| descripcion | text | | | |
| fecha | timestamptz | | now() | |

---

### `movimientos_mensuales`
Resumen mensual por cuenta (agregados para scoring). PK entera con secuencia.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | int | NN | nextval(seq) | PK |
| user_id | uuid | NN | | |
| cuenta_id | uuid | | | FK → cuentas.id |
| periodo | text | NN | | ej. 'YYYY-MM' |
| abonos_mes | numeric | | 0 | |
| cargos_mes | numeric | | 0 | |
| saldo_fin_mes | numeric | | 0 | |
| num_transacciones | int | | 0 | |
| created_at | timestamptz | | now() | |

UQ: `(user_id, cuenta_id, periodo)`.

---

### `historial_credito`
Historial de créditos del cliente.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| cliente_id | uuid | | | (sin FK declarada) |
| monto | numeric | NN | | |
| cuotas | int | NN | | |
| tasa | numeric | NN | | |
| estado | text | | 'vigente' | |
| fecha_inicio | date | | | |
| fecha_fin | date | | | |
| created_at | timestamptz | | now() | |

---

### `oficiales`
Oficiales de crédito (catálogo alterno). PK `uuid` **sin** default.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | | PK |
| nombre | text | NN | | |
| apellidos | text | NN | | |
| dni | text | | | UQ |
| zona | text | | | |
| telefono | text | | | |
| created_at | timestamptz | | now() | |

---

### `solicitudes`
Solicitud simple (flujo legado, distinto de `solicitudes_credito`).

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| cliente_id | uuid | | | (sin FK declarada) |
| oficial_id | uuid | | | FK → oficiales.id |
| monto_solicitado | numeric | NN | | |
| cuotas | int | NN | | |
| destino | text | | | |
| estado | text | | 'enviado' | |
| url_dni_frontal | text | | | |
| url_dni_posterior | text | | | |
| url_doc_extra | text | | | |
| observaciones | text | | | |
| sincronizado | bool | | false | |
| created_at | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

---

### `documentos`
Documentos asociados a `solicitudes` (flujo legado).

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| solicitud_id | uuid | | | FK → solicitudes.id |
| tipo | text | NN | | |
| url_storage | text | NN | | |
| created_at | timestamptz | | now() | |

---

## App del cliente

### `cliente_app_auth`
Credenciales de acceso del cliente a su app.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| cliente_id | uuid | NN | | FK → clientes.id |
| usuario | varchar | NN | | UQ |
| password_hash | text | NN | | |
| estado | varchar | NN | 'activo' | |
| ultimo_login | timestamptz | | | |
| created_at | timestamptz | | now() | |
| updated_at | timestamptz | | now() | |

---

### `cliente_dispositivos`
Dispositivos / tokens push del cliente.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| cliente_id | uuid | NN | | FK → clientes.id |
| token_fcm | text | NN | | |
| plataforma | varchar | | | |
| activo | bool | | true | |
| created_at | timestamptz | | now() | |

---

### `cliente_documentos`
Documentos del cliente (opcionalmente ligados a un crédito).

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| cliente_id | uuid | NN | | FK → clientes.id |
| credito_id | uuid | | | FK → creditos.id |
| tipo_documento | varchar | | | |
| url_archivo | text | NN | | |
| created_at | timestamptz | | now() | |

---

### `cliente_notificaciones`
Notificaciones in-app del cliente.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| cliente_id | uuid | NN | | FK → clientes.id |
| titulo | varchar | NN | | |
| mensaje | text | NN | | |
| leida | bool | | false | |
| fecha_envio | timestamptz | | now() | |

---

### `cliente_soporte`
Tickets de soporte del cliente.

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| cliente_id | uuid | NN | | FK → clientes.id |
| asunto | varchar | | | |
| mensaje | text | | | |
| estado | varchar | | 'abierto' | |
| created_at | timestamptz | | now() | |

---

### `auth_mock`
Tabla auxiliar de autenticación (mock/desarrollo).

| Columna | Tipo | Null | Default | Notas |
|---|---|---|---|---|
| id | uuid | NN | gen_random_uuid() | PK |
| email | text | NN | | UQ |
| created_at | timestamptz | | now() | |

---

## Resumen de llaves foráneas

| Tabla | Columna | Referencia |
|---|---|---|
| acciones_cobranza | cliente_id | clientes.id |
| acciones_cobranza | asesor_id | asesores_negocio.id |
| acciones_cobranza | credito_id | creditos.id |
| alertas_cartera | cliente_id | clientes.id |
| alertas_cartera | asesor_id | asesores_negocio.id |
| alertas_cartera | credito_id | creditos.id |
| asesores_negocio | agencia_id | agencias.id |
| campanas_activas | asesor_id | asesores_negocio.id |
| campanas_activas | cliente_id | clientes.id |
| cartera_diaria | credito_id | creditos.id |
| cartera_diaria | asesor_id | asesores_negocio.id |
| cartera_diaria | cliente_id | clientes.id |
| cartera_diaria | agencia_id | agencias.id |
| cliente_app_auth | cliente_id | clientes.id |
| cliente_dispositivos | cliente_id | clientes.id |
| cliente_documentos | credito_id | creditos.id |
| cliente_documentos | cliente_id | clientes.id |
| cliente_notificaciones | cliente_id | clientes.id |
| cliente_soporte | cliente_id | clientes.id |
| clientes | asesor_id | asesores_negocio.id |
| clientes | agencia_id | agencias.id |
| consultas_buro | asesor_id | asesores_negocio.id |
| consultas_buro | solicitud_id | solicitudes_credito.id |
| consultas_buro | consulta_original_id | consultas_buro.id |
| consultas_buro | cliente_id | clientes.id |
| creditos | agencia_id | agencias.id |
| creditos | cliente_id | clientes.id |
| creditos | asesor_id | asesores_negocio.id |
| creditos_preaprobados | asesor_id | asesores_negocio.id |
| creditos_preaprobados | cliente_id | clientes.id |
| cronograma_cuotas | credito_id | creditos.id |
| cronograma_cuotas | cliente_id | clientes.id |
| documentos | solicitud_id | solicitudes.id |
| fichas_campo | score_id | scores_transaccionales.id |
| movimientos_mensuales | cuenta_id | cuentas.id |
| pagos | credito_id | creditos.id |
| pagos | cliente_id | clientes.id |
| pagos | cuota_id | cronograma_cuotas.id |
| solicitudes | oficial_id | oficiales.id |
| solicitudes_credito | cliente_id | clientes.id |
| solicitudes_credito | asesor_id | asesores_negocio.id |
| solicitudes_credito | agencia_id | agencias.id |
| solicitudes_documentos | solicitud_id | solicitudes_credito.id |
| solicitudes_notas_internas | solicitud_id | solicitudes_credito.id |
| solicitudes_notas_internas | asesor_id | asesores_negocio.id |
| transacciones | cuenta_id | cuentas.id |

---

## Notas / consideraciones para Cursor

1. **Dos flujos de solicitud coexisten**: `solicitudes_credito` (flujo principal multi-paso, con `solicitudes_documentos` y `solicitudes_notas_internas`) y `solicitudes` + `documentos` + `oficiales` (flujo legado más simple). No mezclarlos.
2. **`user_id` vs `cliente_id`**: las tablas de scoring (`scores_transaccionales`, `features_scoring`, `perfiles_clientes`, `fichas_campo`, `cuentas`, `transacciones`, `movimientos_mensuales`) usan `user_id` sin FK formal. Asumir que `user_id` mapea al cliente por convención de aplicación, no por integridad referencial de la BD.
3. **Geolocalización** presente en varias tablas (`lat`/`lng`, `lat_visita`, `lat_captura`) para trazabilidad de visitas y capturas en campo.
4. **Offline-first**: `solicitudes_credito.pendiente_sync` y `solicitudes.sincronizado` indican sincronización diferida desde la app de campo.
5. **Firmas y consentimientos** se guardan en base64 (`firma_cliente_base64`, `firma_consentimiento_base64`).
6. **`oficiales.id`** no tiene default `gen_random_uuid()`: el id debe generarse desde la aplicación al insertar.
7. **Moneda** por defecto `PEN`; calificaciones y deudas siguen nomenclatura **SBS** (Perú).
8. **M6 — Cronograma de Pagos** (`cronograma_cuotas`, `pagos`): son las **únicas** tablas con desglose de cuotas y pagos. `creditos` solo guarda agregados (`saldo_actual`, `cuotas_pagadas`, `monto_vencido`); el **detalle** vive en estas tablas. Definir el core/backend como fuente de verdad: recalcula los agregados de `creditos` a partir de `cronograma_cuotas`/`pagos`. No duplicar lógica de cálculo en el cliente.
9. **M6 es read-only en el cliente**: `cronograma_cuotas` y `pagos` se sincronizan hacia abajo (cache SQLite, TTL vía `updated_at`). La escritura es exclusiva de `service_role` (no hay políticas RLS de INSERT/UPDATE/DELETE). El cliente nunca registra pagos ni cuotas.
10. **`cliente_id` denormalizado en M6**: `cronograma_cuotas` y `pagos` repiten `cliente_id` (además de `credito_id`) a propósito, para RLS sin JOIN y filtrado offline. Mantenerlo consistente con el `cliente_id` del crédito al insertar desde el core.
11. **RLS de M6 depende de `current_cliente_id()`**: esa función resuelve el cliente autenticado desde un claim JWT `cliente_id`. Debe estar alineada con el esquema de auth de M2; si no entrega el claim, las consultas del cliente devuelven 0 filas.