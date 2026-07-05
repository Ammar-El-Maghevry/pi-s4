import { useEffect, useState, type FormEvent } from "react";
import {
  createCamera,
  deleteCamera,
  listCameras,
  testCameraConnection,
  updateCamera,
} from "../api/cameras";
import { extractErrorMessage, extractErrorStatus } from "../api/client";
import type { CameraRead } from "../types/api";
import { Button, Card, ErrorBanner, Input, Label, SuccessBanner } from "../components/ui";

const emptyCreateForm = { name: "", location: "", source_url: "" };

interface EditForm {
  name: string;
  location: string;
  source_url: string;
  is_active: boolean;
  present_threshold: string;
  late_threshold: string;
  face_match_threshold: string;
}

function toEditForm(c: CameraRead): EditForm {
  return {
    name: c.name,
    location: c.location ?? "",
    source_url: c.source_url, // valeur masquée reçue du GET — voir note ci-dessous
    is_active: c.is_active,
    present_threshold: String(c.present_threshold),
    late_threshold: String(c.late_threshold),
    face_match_threshold: String(c.face_match_threshold),
  };
}

export function CamerasPage() {
  const [cameras, setCameras] = useState<CameraRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [createForm, setCreateForm] = useState(emptyCreateForm);
  const [createStatus, setCreateStatus] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const [testResult, setTestResult] = useState<string | null>(null);

  const refetch = async () => {
    setLoading(true);
    setListError(null);
    try {
      const data = await listCameras();
      setCameras(data);
      if (selectedId != null) {
        const updated = data.find((c) => c.id === selectedId);
        if (updated) setEditForm(toEditForm(updated));
      }
    } catch (err) {
      setListError(`${extractErrorStatus(err) ?? "?"} — ${extractErrorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreateStatus(null);
    try {
      const created = await createCamera({
        name: createForm.name,
        location: createForm.location || null,
        source_url: createForm.source_url,
      });
      setCreateStatus(`201 — caméra #${created.id} créée`);
      setCreateForm(emptyCreateForm);
      await refetch();
    } catch (err) {
      setCreateError(`${extractErrorStatus(err) ?? "?"} — ${extractErrorMessage(err)}`);
    }
  };

  const select = (c: CameraRead) => {
    setSelectedId(c.id);
    setEditForm(toEditForm(c));
    setSaveStatus(null);
    setSaveError(null);
    setTestResult(null);
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    if (selectedId == null || editForm == null) return;
    setSaveError(null);
    setSaveStatus(null);
    try {
      await updateCamera(selectedId, {
        name: editForm.name,
        location: editForm.location || null,
        source_url: editForm.source_url,
        is_active: editForm.is_active,
        present_threshold: Number(editForm.present_threshold),
        late_threshold: Number(editForm.late_threshold),
        face_match_threshold: Number(editForm.face_match_threshold),
      });
      setSaveStatus("200 — caméra mise à jour (les identifiants réels ne sont pas écrasés)");
      await refetch();
    } catch (err) {
      setSaveError(`${extractErrorStatus(err) ?? "?"} — ${extractErrorMessage(err)}`);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteCamera(id);
      if (selectedId === id) {
        setSelectedId(null);
        setEditForm(null);
      }
      await refetch();
    } catch (err) {
      setListError(`${extractErrorStatus(err) ?? "?"} — ${extractErrorMessage(err)}`);
    }
  };

  const handleTest = async () => {
    if (selectedId == null) return;
    setTestResult(null);
    try {
      const result = await testCameraConnection(selectedId);
      setTestResult(
        `${result.success ? "OK" : "Échec"} — ${result.message}` +
          (result.width ? ` (${result.width}x${result.height})` : ""),
      );
    } catch (err) {
      setTestResult(`${extractErrorStatus(err) ?? "?"} — ${extractErrorMessage(err)}`);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Caméras</h1>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-200">
          Ajouter une caméra
        </h2>
        <form onSubmit={handleCreate} className="grid grid-cols-1 gap-3 sm:grid-cols-4">
          <div>
            <Label>Nom</Label>
            <Input
              required
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
            />
          </div>
          <div>
            <Label>Emplacement</Label>
            <Input
              value={createForm.location}
              onChange={(e) => setCreateForm({ ...createForm, location: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <Label>Source (RTSP ou index USB)</Label>
            <Input
              required
              placeholder="rtsp://user:pass@host:554/stream"
              value={createForm.source_url}
              onChange={(e) => setCreateForm({ ...createForm, source_url: e.target.value })}
            />
          </div>
          <div className="sm:col-span-4">
            <Button type="submit">Ajouter</Button>
          </div>
          <div className="sm:col-span-4 space-y-2">
            <ErrorBanner message={createError} />
            <SuccessBanner message={createStatus} />
          </div>
        </form>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200">
              Liste ({cameras.length})
            </h2>
            <Button variant="secondary" onClick={refetch}>
              Rafraîchir
            </Button>
          </div>
          <ErrorBanner message={listError} />
          {loading ? (
            <p className="text-sm text-gray-400">Chargement...</p>
          ) : (
            <ul className="space-y-2">
              {cameras.map((c) => (
                <li
                  key={c.id}
                  className={`rounded-md border p-3 text-sm ${
                    selectedId === c.id
                      ? "border-blue-400 bg-blue-50 dark:border-blue-700 dark:bg-blue-950"
                      : "border-gray-200 dark:border-gray-800"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{c.name}</p>
                      <p className="font-mono text-xs text-gray-500 dark:text-gray-400">
                        {c.source_url}
                      </p>
                      <p className="text-xs text-gray-400">
                        {c.is_active ? "active" : "inactive"} · présent ≥ {c.present_threshold} ·
                        retard ≥ {c.late_threshold}
                      </p>
                    </div>
                    <div className="flex shrink-0 gap-1">
                      <Button variant="secondary" onClick={() => select(c)}>
                        Configurer
                      </Button>
                      <Button variant="danger" onClick={() => handleDelete(c.id)}>
                        Supprimer
                      </Button>
                    </div>
                  </div>
                </li>
              ))}
              {cameras.length === 0 && <p className="text-sm text-gray-400">Aucune caméra.</p>}
            </ul>
          )}
        </Card>

        <Card>
          <h2 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-200">
            Configuration {selectedId != null ? `— caméra #${selectedId}` : ""}
          </h2>
          {editForm == null ? (
            <p className="text-sm text-gray-400">
              Sélectionnez une caméra dans la liste pour voir/modifier sa configuration.
            </p>
          ) : (
            <form onSubmit={handleSave} className="space-y-3">
              <div>
                <Label>Nom</Label>
                <Input
                  required
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                />
              </div>
              <div>
                <Label>Emplacement</Label>
                <Input
                  value={editForm.location}
                  onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
                />
              </div>
              <div>
                <Label>Source (rtsp://user:pass@host/...)</Label>
                <Input
                  value={editForm.source_url}
                  onChange={(e) => setEditForm({ ...editForm, source_url: e.target.value })}
                />
                <p className="mt-1 text-xs text-gray-400">
                  Le mot de passe est masqué (***) tel que renvoyé par l'API. Si vous
                  n'y touchez pas et enregistrez, le backend doit préserver les
                  identifiants réels en base plutôt que d'écraser avec la valeur masquée.
                </p>
              </div>
              <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
                <input
                  type="checkbox"
                  checked={editForm.is_active}
                  onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                />
                Caméra active
              </label>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <Label>Seuil présent</Label>
                  <Input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={editForm.present_threshold}
                    onChange={(e) =>
                      setEditForm({ ...editForm, present_threshold: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label>Seuil retard</Label>
                  <Input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={editForm.late_threshold}
                    onChange={(e) => setEditForm({ ...editForm, late_threshold: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Seuil visage</Label>
                  <Input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={editForm.face_match_threshold}
                    onChange={(e) =>
                      setEditForm({ ...editForm, face_match_threshold: e.target.value })
                    }
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button type="submit">Enregistrer</Button>
                <Button type="button" variant="secondary" onClick={handleTest}>
                  Tester la connexion
                </Button>
              </div>
              <ErrorBanner message={saveError} />
              <SuccessBanner message={saveStatus} />
              {testResult && (
                <p className="text-sm text-gray-600 dark:text-gray-300">{testResult}</p>
              )}
            </form>
          )}
        </Card>
      </div>
    </div>
  );
}
