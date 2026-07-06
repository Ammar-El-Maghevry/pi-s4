export function TableLoading({ colSpan }: { colSpan: number }) {
  return (
    <tr>
      <td colSpan={colSpan} className="py-10 text-center text-sm text-text-muted">
        Loading…
      </td>
    </tr>
  );
}

export function TableEmpty({ colSpan, message = "No records found." }: { colSpan: number; message?: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="py-10 text-center text-sm text-text-muted">
        {message}
      </td>
    </tr>
  );
}
