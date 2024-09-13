interface DetailEntityProps {
  icon: React.ReactNode;
  children?: React.ReactNode;
}

export default function DetailEntity({ icon, children }: DetailEntityProps) {
  return (
    <div className="flex gap-2 items-center [&>svg]:size-4">
      {icon}
      <p className="font-medium">{children}</p>
    </div>
  );
}
