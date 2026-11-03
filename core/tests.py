from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from solucion import ACEPTADO

from .models import Producto, Registro
from .services import registrar_retiro


class RegistroWorkflowTests(TestCase):
    def setUp(self):
        self.arroz, _ = Producto.objects.update_or_create(nombre="arroz", defaults={"stock": 3})
        self.fideos, _ = Producto.objects.update_or_create(nombre="fideos", defaults={"stock": 5})

        self.grupos = {
            name: Group.objects.create(name=name)
            for name in ("admin", "normal", "viewer")
        }
        self.admin = User.objects.create_user("admin_prueba")
        self.normal = User.objects.create_user("normal_prueba")
        self.viewer = User.objects.create_user("viewer_prueba")
        self.sin_grupo = User.objects.create_user("sin_grupo")
        self.admin.groups.add(self.grupos["admin"])
        self.normal.groups.add(self.grupos["normal"])
        self.viewer.groups.add(self.grupos["viewer"])

    def test_normal_puede_crear_retiro_y_se_descuenta_stock(self):
        self.client.force_login(self.normal)

        response = self.client.post(
            reverse("crear"),
            {"producto": "arroz", "cantidad_solicitada": "2"},
        )

        self.assertRedirects(response, reverse("lista"))
        self.arroz.refresh_from_db()
        registro = Registro.objects.get()
        self.assertEqual(self.arroz.stock, 1)
        self.assertEqual(registro.resultado, ACEPTADO)
        self.assertTrue(registro.afecta_stock)

    def test_retiro_mayor_al_stock_no_cae_y_no_descuenta_inventario(self):
        self.client.force_login(self.normal)

        response = self.client.post(
            reverse("crear"),
            {"producto": "arroz", "cantidad_solicitada": "4"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [(reverse("lista"), 302)])
        self.assertContains(response, "Rechazo: Fuera de stock")
        self.arroz.refresh_from_db()
        registro = Registro.objects.get()
        self.assertEqual(self.arroz.stock, 3)
        self.assertEqual(registro.resultado, "Rechazo: Fuera de stock")
        self.assertFalse(registro.afecta_stock)

    def test_editar_retiro_recalcula_y_ajusta_ambos_stocks(self):
        registro = registrar_retiro("arroz", 2)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("editar", args=[registro.pk]),
            {"producto": "fideos", "cantidad_solicitada": "1"},
        )

        self.assertRedirects(response, reverse("lista"))
        self.arroz.refresh_from_db()
        self.fideos.refresh_from_db()
        registro.refresh_from_db()
        self.assertEqual(self.arroz.stock, 3)
        self.assertEqual(self.fideos.stock, 4)
        self.assertEqual(registro.producto, "fideos")
        self.assertEqual(registro.cantidad_solicitada, 1)
        self.assertEqual(registro.resultado, ACEPTADO)

    def test_eliminar_retiro_restaura_stock_y_conserva_registro(self):
        registro = registrar_retiro("arroz", 2)
        self.client.force_login(self.admin)

        response = self.client.post(reverse("eliminar", args=[registro.pk]))

        self.assertRedirects(response, reverse("lista"))
        self.arroz.refresh_from_db()
        registro.refresh_from_db()
        self.assertEqual(self.arroz.stock, 3)
        self.assertTrue(registro.eliminado)
        self.assertIsNotNone(registro.fecha_eliminacion)
        self.assertEqual(Registro.objects.count(), 1)

    def test_rol_sin_permisos_no_puede_crear_editar_ni_eliminar(self):
        registro = registrar_retiro("arroz", 2)
        self.client.force_login(self.viewer)

        crear = self.client.post(
            reverse("crear"),
            {"producto": "fideos", "cantidad_solicitada": "1"},
        )
        editar = self.client.post(
            reverse("editar", args=[registro.pk]),
            {"producto": "fideos", "cantidad_solicitada": "1"},
        )
        eliminar = self.client.post(reverse("eliminar", args=[registro.pk]))

        self.assertEqual(crear.status_code, 302)
        self.assertEqual(editar.status_code, 302)
        self.assertEqual(eliminar.status_code, 302)
        self.arroz.refresh_from_db()
        self.fideos.refresh_from_db()
        registro.refresh_from_db()
        self.assertEqual(Registro.objects.count(), 1)
        self.assertEqual(self.arroz.stock, 1)
        self.assertEqual(self.fideos.stock, 5)
        self.assertEqual(registro.producto, "arroz")
        self.assertFalse(registro.eliminado)

        self.client.force_login(self.sin_grupo)
        sin_grupo = self.client.post(
            reverse("crear"),
            {"producto": "fideos", "cantidad_solicitada": "1"},
        )
        self.assertEqual(sin_grupo.status_code, 302)
        self.assertEqual(Registro.objects.count(), 1)

    def test_cantidades_fuera_de_rango_se_validan_sin_error_500(self):
        cantidades_fuera_de_rango = (
            "10001",
            "99999999999999999999",
            "-99999999999999999999",
        )
        self.client.force_login(self.normal)

        for cantidad in cantidades_fuera_de_rango:
            with self.subTest(operacion="crear", cantidad=cantidad):
                response = self.client.post(
                    reverse("crear"),
                    {"producto": "arroz", "cantidad_solicitada": cantidad},
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("cantidad_solicitada", response.context["form"].errors)
                self.assertEqual(Registro.objects.count(), 0)

        self.arroz.refresh_from_db()
        self.assertEqual(self.arroz.stock, 3)

        registro = registrar_retiro("arroz", 1)
        self.client.force_login(self.admin)

        for cantidad in cantidades_fuera_de_rango:
            with self.subTest(operacion="editar", cantidad=cantidad):
                response = self.client.post(
                    reverse("editar", args=[registro.pk]),
                    {"producto": "fideos", "cantidad_solicitada": cantidad},
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("cantidad_solicitada", response.context["form"].errors)
                registro.refresh_from_db()
                self.arroz.refresh_from_db()
                self.fideos.refresh_from_db()
                self.assertEqual(registro.producto, "arroz")
                self.assertEqual(registro.cantidad_solicitada, 1)
                self.assertEqual(self.arroz.stock, 2)
                self.assertEqual(self.fideos.stock, 5)

    def test_cero_y_negativo_razonable_siguen_llegando_a_decidir(self):
        self.client.force_login(self.normal)

        for cantidad in ("0", "-1"):
            with self.subTest(cantidad=cantidad):
                response = self.client.post(
                    reverse("crear"),
                    {"producto": "arroz", "cantidad_solicitada": cantidad},
                )
                self.assertRedirects(response, reverse("lista"))
                registro = Registro.objects.latest("pk")
                self.assertEqual(registro.resultado, "Error: Cantidad inválida")
                self.assertFalse(registro.afecta_stock)

        self.arroz.refresh_from_db()
        self.assertEqual(self.arroz.stock, 3)


class RegistroAPITests(TestCase):
    password = "clave-temporal-pruebas"

    def setUp(self):
        self.arroz, _ = Producto.objects.update_or_create(nombre="arroz", defaults={"stock": 3})
        self.fideos, _ = Producto.objects.update_or_create(nombre="fideos", defaults={"stock": 5})
        self.grupos = {
            nombre: Group.objects.get_or_create(name=nombre)[0]
            for nombre in ("admin", "normal", "viewer")
        }
        self.usuarios = {
            nombre: User.objects.create_user(nombre, password=self.password)
            for nombre in self.grupos
        }
        for nombre, usuario in self.usuarios.items():
            usuario.groups.add(self.grupos[nombre])
        self.client = APIClient()

    def autenticar(self, nombre):
        respuesta = self.client.post(
            reverse("api_token"),
            {"username": nombre, "password": self.password},
            format="json",
        )
        self.assertEqual(respuesta.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {respuesta.data['access']}"
        )
        return respuesta.data

    def test_api_exige_token_para_consultar(self):
        respuesta = self.client.get("/api/registros/")

        self.assertEqual(respuesta.status_code, 401)

    def test_api_no_acepta_tokens_drf_sin_vencimiento(self):
        token = Token.objects.create(user=self.usuarios["normal"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        respuesta = self.client.get("/api/registros/")

        self.assertEqual(respuesta.status_code, 401)

    def test_normal_crea_y_el_servidor_calcula_el_resultado(self):
        self.autenticar("normal")

        respuesta = self.client.post(
            "/api/registros/",
            {
                "producto": "  ARROZ  ",
                "cantidad_solicitada": 2,
                "resultado": "Rechazo: Fuera de stock",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.data["producto"], "arroz")
        self.assertEqual(respuesta.data["resultado"], ACEPTADO)
        self.assertNotIn("afecta_stock", respuesta.data)
        self.arroz.refresh_from_db()
        self.assertEqual(self.arroz.stock, 1)

    def test_admin_edita_y_elimina_restaura_el_stock(self):
        registro = registrar_retiro("arroz", 2)
        self.autenticar("admin")

        actualizar = self.client.patch(
            f"/api/registros/{registro.pk}/",
            {"producto": "fideos", "cantidad_solicitada": 1},
            format="json",
        )

        self.assertEqual(actualizar.status_code, 200)
        self.arroz.refresh_from_db()
        self.fideos.refresh_from_db()
        self.assertEqual(self.arroz.stock, 3)
        self.assertEqual(self.fideos.stock, 4)

        borrar = self.client.delete(f"/api/registros/{registro.pk}/")

        self.assertEqual(borrar.status_code, 204)
        self.arroz.refresh_from_db()
        self.fideos.refresh_from_db()
        registro.refresh_from_db()
        self.assertEqual(self.arroz.stock, 3)
        self.assertEqual(self.fideos.stock, 5)
        self.assertTrue(registro.eliminado)
        self.assertIsNotNone(registro.fecha_eliminacion)
        self.assertEqual(
            self.client.get(f"/api/registros/{registro.pk}/").status_code,
            404,
        )

    def test_put_reemplaza_campos_y_recalcula_stock(self):
        registro = registrar_retiro("arroz", 1)
        self.autenticar("admin")

        respuesta = self.client.put(
            f"/api/registros/{registro.pk}/",
            {"producto": "fideos", "cantidad_solicitada": 2},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 200)
        self.arroz.refresh_from_db()
        self.fideos.refresh_from_db()
        self.assertEqual(self.arroz.stock, 3)
        self.assertEqual(self.fideos.stock, 3)

    def test_viewer_no_escribe_y_entrada_invalida_devuelve_400(self):
        self.autenticar("viewer")

        sin_permiso = self.client.post(
            "/api/registros/",
            {"producto": "arroz", "cantidad_solicitada": 1},
            format="json",
        )
        invalida = self.client.post(
            "/api/registros/",
            {"producto": "arroz", "cantidad_solicitada": 10001},
            format="json",
        )

        self.assertEqual(sin_permiso.status_code, 403)
        self.assertEqual(invalida.status_code, 403)
        self.assertEqual(Registro.objects.count(), 0)

        self.autenticar("normal")
        invalida = self.client.post(
            "/api/registros/",
            {"producto": "arroz", "cantidad_solicitada": 10001},
            format="json",
        )
        self.assertEqual(invalida.status_code, 400)
        self.assertIn("cantidad_solicitada", invalida.data)
        self.assertEqual(Registro.objects.count(), 0)

    def test_listado_pagina_en_bloques_de_diez(self):
        self.autenticar("viewer")
        Registro.objects.bulk_create(
            [
                Registro(
                    producto="arroz",
                    cantidad_solicitada=1,
                    resultado="Rechazo: Fuera de stock",
                )
                for _ in range(11)
            ]
        )

        respuesta = self.client.get("/api/registros/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["count"], 11)
        self.assertEqual(len(respuesta.data["results"]), 10)
        self.assertIsNotNone(respuesta.data["next"])

    def test_refresh_se_rota_y_los_tokens_revocados_no_se_reutilizan(self):
        tokens = self.autenticar("normal")
        self.client.credentials()

        rotacion = self.client.post(
            reverse("api_token_refresh"),
            {"refresh": tokens["refresh"]},
            format="json",
        )
        self.assertEqual(rotacion.status_code, 200)

        refresh_anterior = self.client.post(
            reverse("api_token_refresh"),
            {"refresh": tokens["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_anterior.status_code, 401)

        refresh_nuevo = rotacion.data["refresh"]
        revocacion = self.client.post(
            reverse("api_token_blacklist"),
            {"refresh": refresh_nuevo},
            format="json",
        )
        self.assertEqual(revocacion.status_code, 200)
        refresh_revocado = self.client.post(
            reverse("api_token_refresh"),
            {"refresh": refresh_nuevo},
            format="json",
        )
        self.assertEqual(refresh_revocado.status_code, 401)
