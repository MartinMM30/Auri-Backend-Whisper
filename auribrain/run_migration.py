from migrate_legacy_memory import migrate_user

if __name__ == "__main__":
    UID = "giDZenjZ1FRM0MpipFS1xCIQJtz1"  # tu UID
    n = migrate_user(UID)
    print(f"✓ Migración completa — {n} hechos importados")
