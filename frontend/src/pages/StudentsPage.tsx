import { useEffect, useState, type FormEvent } from "react";
import { createStudent, deleteStudent, listStudents, updateStudent } from "../api/students";
import { extractErrorMessage, extractErrorStatus } from "../api/client";
import type { StudentRead } from "../types/api";
import { Button, Card, ErrorBanner, Input, Label, SuccessBanner } from "../components/ui";

const emptyForm = { full_name: "", student_id: "", email: "", department: "" };

export function StudentsPage() {
  const [students, setStudents] = useState<StudentRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [form, setForm] = useState(emptyForm);
  const [createStatus, setCreateStatus] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState(emptyForm);
  const [rowStatus, setRowStatus] = useState<{ id: number; message: string; ok: boolean } | null>(
    null,
  );

  const refetch = async () => {
    setLoading(true);
    setListError(null);
    try {
      setStudents(await listStudents());
    } catch (err) {
      setListError(`${extractErrorStatus(err) ?? "?"} — ${extractErrorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refetch();
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreateStatus(null);
    try {
      const created = await createStudent({
        full_name: form.full_name,
        student_id: form.student_id,
        email: form.email || null,
        department: form.department || null,
      });
      setCreateStatus(`201 — étudiant #${created.id} créé`);
      setForm(emptyForm);
      await refetch();
    } catch (err) {
      setCreateError(`${extractErrorStatus(err) ?? "?"} — ${extractErrorMessage(err)}`);
    }
  };

  const startEdit = (s: StudentRead) => {
    setEditingId(s.id);
    setEditForm({
      full_name: s.full_name,
      student_id: s.student_id,
      email: s.email ?? "",
      department: s.department ?? "",
    });
    setRowStatus(null);
  };

  const handleUpdate = async (id: number) => {
    try {
      await updateStudent(id, {
        full_name: editForm.full_name,
        student_id: editForm.student_id,
        email: editForm.email || null,
        department: editForm.department || null,
      });
      setRowStatus({ id, message: "200 — mis à jour", ok: true });
      setEditingId(null);
      await refetch();
    } catch (err) {
      setRowStatus({
        id,
        message: `${extractErrorStatus(err) ?? "?"} — ${extractErrorMessage(err)}`,
        ok: false,
      });
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteStudent(id);
      setRowStatus({ id, message: "204 — supprimé", ok: true });
      await refetch();
    } catch (err) {
      setRowStatus({
        id,
        message: `${extractErrorStatus(err) ?? "?"} — ${extractErrorMessage(err)}`,
        ok: false,
      });
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Étudiants</h1>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-200">
          Ajouter un étudiant
        </h2>
        <form onSubmit={handleCreate} className="grid grid-cols-1 gap-3 sm:grid-cols-4">
          <div>
            <Label>Nom complet</Label>
            <Input
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </div>
          <div>
            <Label>Matricule</Label>
            <Input
              required
              value={form.student_id}
              onChange={(e) => setForm({ ...form, student_id: e.target.value })}
            />
          </div>
          <div>
            <Label>Email</Label>
            <Input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </div>
          <div>
            <Label>Département</Label>
            <Input
              value={form.department}
              onChange={(e) => setForm({ ...form, department: e.target.value })}
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

      <Card>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200">
            Liste ({students.length})
          </h2>
          <Button variant="secondary" onClick={refetch}>
            Rafraîchir
          </Button>
        </div>
        <ErrorBanner message={listError} />
        {loading ? (
          <p className="text-sm text-gray-400">Chargement...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-gray-500 dark:border-gray-800 dark:text-gray-400">
                  <th className="py-2 pr-2">Matricule</th>
                  <th className="py-2 pr-2">Nom</th>
                  <th className="py-2 pr-2">Email</th>
                  <th className="py-2 pr-2">Département</th>
                  <th className="py-2 pr-2">Visage</th>
                  <th className="py-2 pr-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {students.map((s) => (
                  <tr key={s.id} className="border-b border-gray-100 dark:border-gray-900">
                    {editingId === s.id ? (
                      <>
                        <td className="py-2 pr-2">
                          <Input
                            value={editForm.student_id}
                            onChange={(e) =>
                              setEditForm({ ...editForm, student_id: e.target.value })
                            }
                          />
                        </td>
                        <td className="py-2 pr-2">
                          <Input
                            value={editForm.full_name}
                            onChange={(e) =>
                              setEditForm({ ...editForm, full_name: e.target.value })
                            }
                          />
                        </td>
                        <td className="py-2 pr-2">
                          <Input
                            value={editForm.email}
                            onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                          />
                        </td>
                        <td className="py-2 pr-2">
                          <Input
                            value={editForm.department}
                            onChange={(e) =>
                              setEditForm({ ...editForm, department: e.target.value })
                            }
                          />
                        </td>
                        <td className="py-2 pr-2 text-gray-400">—</td>
                        <td className="py-2 pr-2 space-x-1 whitespace-nowrap">
                          <Button onClick={() => handleUpdate(s.id)}>Enregistrer</Button>
                          <Button variant="secondary" onClick={() => setEditingId(null)}>
                            Annuler
                          </Button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="py-2 pr-2 text-gray-900 dark:text-gray-100">{s.student_id}</td>
                        <td className="py-2 pr-2 text-gray-900 dark:text-gray-100">{s.full_name}</td>
                        <td className="py-2 pr-2 text-gray-600 dark:text-gray-400">{s.email ?? "—"}</td>
                        <td className="py-2 pr-2 text-gray-600 dark:text-gray-400">
                          {s.department ?? "—"}
                        </td>
                        <td className="py-2 pr-2 text-gray-600 dark:text-gray-400">
                          {s.has_face_embedding ? "oui" : "non"}
                        </td>
                        <td className="py-2 pr-2 space-x-1 whitespace-nowrap">
                          <Button variant="secondary" onClick={() => startEdit(s)}>
                            Modifier
                          </Button>
                          <Button variant="danger" onClick={() => handleDelete(s.id)}>
                            Supprimer
                          </Button>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
                {students.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-4 text-center text-gray-400">
                      Aucun étudiant.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            {rowStatus && (
              <p
                className={`mt-2 text-sm ${
                  rowStatus.ok
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                }`}
              >
                Étudiant #{rowStatus.id} : {rowStatus.message}
              </p>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
