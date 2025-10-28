## Firma de correos para recuperación de contraseña

Ahora el email de recuperación usa plantillas HTML/TXT con una firma configurable.

- Plantillas: `templates/email/reset_password.html` y `templates/email/reset_password.txt`.
- Variables de entorno para personalizar la firma (edítalas en tu `.env`):

```
# Datos de firma
SIGN_NAME=Yeivi Julieth Peinado H.
SIGN_TITLE=Gerente de Servicios Ciberseguridad
SIGN_PHONE=+57 3013407054
SIGN_LOCATION=Bogotá, Colombia
SIGN_WEBSITE=https://www.axity.com
# Imagen/banner opcional con URL pública (deja vacío para ocultar)
SIGN_BANNER_URL=https://tuservidor/imagenes/axity-banner.png
```

Si `SIGN_BANNER_URL` está vacío, no se mostrará la imagen.

Para cambiar el estilo o el contenido, edita las plantillas en `templates/email/`.

