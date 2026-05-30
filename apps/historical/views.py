import logging

from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from .forms import CSVUploadForm
from .models import HistoricalData, UploadedCSV
from .services import bulk_insert, parse_csv

logger = logging.getLogger(__name__)


class HistoricalListView(ListView):
    model = HistoricalData
    template_name = "historical/list.html"
    context_object_name = "data_list"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(Q(date__icontains=search))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search"] = self.request.GET.get("q", "")
        return ctx


class UploadCSVView(FormView):
    form_class = CSVUploadForm
    template_name = "historical/upload.html"
    success_url = reverse_lazy("historical:list")

    def form_valid(self, form):
        uploaded = form.save()
        rows, errors = parse_csv(uploaded.file)

        if errors:
            uploaded.status = "error"
            uploaded.save()
            for err in errors[:20]:
                messages.error(self.request, err)
            if len(errors) > 20:
                messages.error(self.request, f"... and {len(errors) - 20} more errors")
            return self.render_to_response(self.get_context_data(form=form))

        if not rows:
            messages.warning(self.request, "CSV file contains no valid rows.")
            uploaded.status = "error"
            uploaded.save()
            return self.render_to_response(self.get_context_data(form=form))

        request = self.request
        request.session["csv_preview"] = {
            "uploaded_id": uploaded.id,
            "rows": [{"date": str(r["date"]), "close": r["close"]} for r in rows],
        }
        ctx = {"rows": rows, "total": len(rows)}
        return render(request, "historical/preview.html", ctx)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


def confirm_upload(request: HttpRequest) -> HttpResponse:
    preview = request.session.pop("csv_preview", None)
    if not preview:
        messages.error(request, "No pending upload to confirm.")
        return redirect("historical:upload")

    rows = preview["rows"]
    inserted = bulk_insert(rows)
    uploaded_id = preview.get("uploaded_id")
    if uploaded_id:
        UploadedCSV.objects.filter(id=uploaded_id).update(status="done")

    messages.success(request, f"Successfully imported {inserted} rows.")
    return redirect("historical:list")


def cancel_upload(request: HttpRequest) -> HttpResponse:
    preview = request.session.pop("csv_preview", None)
    if preview:
        uploaded_id = preview.get("uploaded_id")
        if uploaded_id:
            UploadedCSV.objects.filter(id=uploaded_id).delete()
        messages.info(request, "Upload cancelled.")
    return redirect("historical:upload")


def delete_historical(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect("historical:list")

    selected_ids = request.POST.getlist("selected_ids")
    if not selected_ids:
        messages.warning(request, "No items selected.")
        return redirect("historical:list")

    deleted, _ = HistoricalData.objects.filter(id__in=selected_ids).delete()
    messages.success(request, f"Deleted {deleted} record(s).")
    return redirect("historical:list")


def delete_all_historical(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect("historical:list")

    count = HistoricalData.objects.count()
    HistoricalData.objects.all().delete()
    messages.success(request, f"Deleted all {count} record(s).")
    return redirect("historical:list")
