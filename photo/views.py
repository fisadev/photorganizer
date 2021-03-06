import glob, shutil, os
from django.shortcuts import render, redirect, get_object_or_404
from photo.models import Folder, ImagenRechazada
from .forms import FormFolder
from photo.logica import listarFotos, acondicionar_ruta, comprobar_carpeta

def home(request):

    if request.method == "POST":
        form = FormFolder(request.POST)

        if form.is_valid():
            folder = form.save(commit=False)

            folder.ruta = acondicionar_ruta(folder.ruta)

            if Folder.objects.filter(ruta=folder.ruta, tipo='origen').exists():

                folder = Folder.objects.get(ruta=folder.ruta, tipo='origen')

            else:
                folder.tipo = 'origen'

                folder.save()

            return redirect('photo.views.visor', pk=folder.id)

    else:
        form = FormFolder()

    return render(
        request,
        'photo/photohome.html',
        {'carpetas': Folder.objects.filter(tipo='origen').order_by('ruta'),
         'form': form}
    )

def visor(request, pk):
    carpetaActual = get_object_or_404(Folder, pk=pk)

    photosList = listarFotos(carpetaActual)

    if request.method == "POST":
        form = FormFolder(request.POST)

        if form.is_valid():
            folder = form.save(commit=False)

            folder.ruta = acondicionar_ruta(folder.ruta)

            if Folder.objects.filter(ruta = folder.ruta, tipo = 'destino').exists():
                folder = Folder.objects.get(ruta = folder.ruta, tipo = 'destino')

            else:
                if comprobar_carpeta(folder.ruta) == "error":
                    return render(
                        request,
                        'photo/visor.html',
                        {'carpetas': Folder.objects.filter(tipo='destino').order_by('ruta'),
                        'form': form,
                        'fotos': photosList,
                        'carpeta': carpetaActual,
                        'error': "No se puede crear la carpeta espcificada"
                        }
                    )
                folder.tipo = 'destino'
                folder.save()

            shutil.move(photosList[0], folder.ruta)

            photosList = listarFotos(carpetaActual)

    else:
        form = FormFolder()

    # es igual a if photoList == []:
    if not photosList:
        if os.path.exists(carpetaActual.ruta):
            return render(
                request,
                'photo/visor.html',
                {'error': "No hay fotos en la carpeta especificada! [verificar que no haya espacios en la ruta]",
                 'carpeta': carpetaActual,
                }
            )
        else:
            return render(
                request,
                'photo/visor.html',
                {'error': "La carpeta especificada no existe",
                 'carpeta': carpetaActual,
                }
            )

    else:
        return render(
            request,
            'photo/visor.html',
            {'carpetas': Folder.objects.filter(tipo='destino').order_by('ruta'),
             'form': form,
             'fotos': photosList,
             'carpeta': carpetaActual,
            }
        )

def eliminar(request, pk, volver, carpeta_actual=None):
    folder = get_object_or_404(Folder, pk=pk)
    folder.delete()
    if volver == 'v':
        return redirect('photo.views.visor', pk=carpeta_actual)
    else:
        return redirect('photo.views.home')


def mover(request, origen, destino):
    origen = get_object_or_404(Folder, pk=origen)
    destino = get_object_or_404(Folder, pk=destino)
    photosList = listarFotos(origen)
    if comprobar_carpeta(destino.ruta) == "error":
        return render(
            request,
            'photo/visor.html',
            {'carpetas': Folder.objects.filter(tipo='destino').order_by('ruta'),
             'form': FormFolder(),
             'fotos': photosList,
             'carpeta': origen,
             'error': "No se puede crear la carpeta espcificada"
            }
        )
    shutil.move(photosList[0], destino.ruta)
    return redirect('photo.views.visor', pk=origen.id)


def rechazar(request, carpeta):
    carpeta = get_object_or_404(Folder, pk=carpeta)
    foto = listarFotos(carpeta)[0]
    foto_rechazada = ImagenRechazada(carpeta=carpeta, ruta=foto)
    foto_rechazada.save()

    return redirect('photo.views.visor', pk=carpeta.id)

def ocultas(request, carpeta):
    carpeta = get_object_or_404(Folder, pk=carpeta)
    imagenes_ocultas = ImagenRechazada.objects.filter(carpeta=carpeta)

    return render (
        request,
        'photo/ocultas.html',
        {'carpeta': carpeta,
         'imagenes': imagenes_ocultas
        }
    )

def restaurar(request, carpeta, pk):
    imagen = get_object_or_404(ImagenRechazada, pk=pk)

    if imagen.ocultar == True:
        imagen.ocultar = False
    else:
        imagen.ocultar = True
    imagen.save()

    return redirect('photo.views.ocultas', carpeta=carpeta)

def desocultar(request, carpeta):
    imagenes_desocultar = ImagenRechazada.objects.filter(ocultar=False)
    for image in imagenes_desocultar:
        image.delete()

    return redirect('photo.views.visor', pk=carpeta)
