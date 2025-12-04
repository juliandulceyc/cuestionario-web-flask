import os

html_content = r'''<!DOCTYPE html>
<html class="light" lang="es">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>Iniciar Sesión - TalentFlow</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com" rel="preconnect"/>
    <link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&amp;display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
    <script>
      tailwind.config = {
        darkMode: "class",
        theme: {
          extend: {
            colors: {
              "primary": "#137fec",
              "background-light": "#f6f7f8",
              "background-dark": "#101922",
            },
            fontFamily: {
              "display": ["Inter", "sans-serif"]
            },
            borderRadius: {
              "DEFAULT": "0.25rem",
              "lg": "0.5rem",
              "xl": "0.75rem",
              "full": "9999px"
            },
          },
        },
      }
    </script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
    </style>
</head>
<body class="bg-background-light dark:bg-background-dark font-display">
<div class="relative flex h-auto min-h-screen w-full flex-col group/design-root overflow-x-hidden">
<div class="layout-container flex h-full grow flex-col">
<div class="flex flex-1 justify-center items-stretch">
<div class="layout-content-container flex flex-col flex-1">
<div class="grid grid-cols-1 md:grid-cols-2 min-h-screen">
<!-- Visual Panel -->
<div class="hidden md:flex flex-col items-center justify-center bg-slate-100 dark:bg-slate-900/50 p-10">
<div class="w-full h-full bg-center bg-no-repeat bg-cover rounded-xl" data-alt="An abstract geometric pattern representing collaboration and professional growth" style='background-image: url("https://lh3.googleusercontent.com/aida-public/AB6AXuBRuPTL3I9tuyIPAc6dIk6B1de6wu9I_F6Ycex7m3CzXeG7m2Sbv14ZT0myAkQCeExdc-u0BpLMmCVwk6mUiCFIYmG6JwatwEPopH4N4CklDcyeXUTdnW49V1VtXCcV7BhdGPxHv8yNGYHhGmvSc1gv1Gl3pB_s9yZHD1GDL2OKwSV57i60LJgOVw1jxxwsiHB3OXcfgfODqjYhTesvo-sUi-0u3gSwV7P3ZWnvb0PhPZVwLMlfo-UxQEXE5YA7I_37VP8EZyAsVtM");'></div>
</div>
<!-- Form Panel -->
<div class="flex flex-col justify-center items-center w-full bg-background-light dark:bg-background-dark px-4 sm:px-6 lg:px-8 py-12">
<div class="flex flex-col w-full max-w-md space-y-8">
<!-- Logo -->
<div class="flex justify-start items-center gap-3">
<div class="bg-primary p-2.5 rounded-lg flex items-center justify-center">
<span class="material-symbols-outlined text-white" style="font-size: 28px;">insights</span>
</div>
<p class="text-xl font-bold text-slate-800 dark:text-slate-200">TalentFlow</p>
</div>
<!-- Headline -->
<div class="w-full">
<h1 class="text-slate-900 dark:text-white tracking-tight text-[32px] font-bold leading-tight text-left">Inicia sesión en tu cuenta</h1>
<p class="text-slate-600 dark:text-slate-400 mt-2">Bienvenido de nuevo, gestiona tus candidatos.</p>
</div>

<!-- Error Message Block -->
{% if error %}
<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative w-full" role="alert">
  <span class="block sm:inline">{{ error }}</span>
</div>
{% endif %}

<form action="{{ url_for('admin_authenticate') }}" method="POST" class="w-full flex flex-col gap-6">
    <!-- Email/Username Field -->
    <label class="flex flex-col w-full">
    <p class="text-slate-800 dark:text-slate-200 text-base font-medium leading-normal pb-2">Usuario o Correo</p>
    <div class="relative flex w-full flex-1 items-stretch">
    <span class="material-symbols-outlined text-slate-400 dark:text-slate-500 absolute left-4 top-1/2 -translate-y-1/2">person</span>
    <input id="username" name="username" class="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-slate-900 dark:text-white focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-slate-300 dark:border-slate-700 bg-background-light dark:bg-background-dark focus:border-primary h-14 placeholder:text-slate-400 dark:placeholder:text-slate-500 pl-12 pr-4 py-3 text-base font-normal leading-normal" placeholder="Ingresa tu usuario" type="text" required value=""/>
    </div>
    </label>
    <!-- Password Field -->
    <label class="flex flex-col w-full">
    <div class="flex justify-between items-baseline pb-2">
    <p class="text-slate-800 dark:text-slate-200 text-base font-medium leading-normal">Contraseña</p>
    </div>
    <div class="relative flex w-full flex-1 items-stretch rounded-lg">
    <span class="material-symbols-outlined text-slate-400 dark:text-slate-500 absolute left-4 top-1/2 -translate-y-1/2">lock</span>
    <input id="password" name="password" class="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-slate-900 dark:text-white focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-slate-300 dark:border-slate-700 bg-background-light dark:bg-background-dark focus:border-primary h-14 placeholder:text-slate-400 dark:placeholder:text-slate-500 pl-12 pr-12 py-3 text-base font-normal leading-normal" placeholder="Introduce tu contraseña" type="password" required value=""/>
    <button type="button" onclick="togglePassword()" aria-label="Toggle password visibility" class="text-slate-400 dark:text-slate-500 absolute right-0 top-0 h-full px-4 flex items-center justify-center">
    <span id="eye-icon" class="material-symbols-outlined">visibility</span>
    </button>
    </div>
    </label>

    <div class="flex justify-end">
    <a class="text-sm font-medium text-primary hover:underline" href="{{ url_for('recuperar_password') }}">¿Olvidaste tu contraseña?</a>
    </div>
    <!-- Login Button -->
    <div class="flex w-full">
    <button type="submit" class="flex min-w-[84px] w-full cursor-pointer items-center justify-center overflow-hidden rounded-lg h-12 px-5 flex-1 bg-primary text-white text-base font-bold leading-normal tracking-[0.015em] hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary/50 dark:focus:ring-offset-background-dark transition-colors">
    <span class="truncate">Iniciar Sesión</span>
    </button>
    </div>
</form>

</div>
</div>
</div>
</div>
</div>
</div>
</div>
<script>
    function togglePassword() {
        const passwordInput = document.getElementById('password');
        const eyeIcon = document.getElementById('eye-icon');
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            eyeIcon.textContent = 'visibility_off';
        } else {
            passwordInput.type = 'password';
            eyeIcon.textContent = 'visibility';
        }
    }
</script>
</body>
</html>'''

file_path = r'c:\Users\USUARIO\Documents\Empresa\templates\admin_login.html'
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html_content)
print(f"Successfully updated {file_path}")
