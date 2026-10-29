import { UserPublic } from "../../api/auth"

export default function EditUserButton({ user_id }: { user_id: number; }) {
  return (
    <a href={`/admin/users/${user_id}`}>
        <button className="btn btn-outline-primary edit-user-button">
        Edytuj
        </button>
    </a>
  )
}