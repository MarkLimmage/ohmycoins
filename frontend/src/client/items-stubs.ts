// Temporary stubs for removed Items functionality
// TODO: Remove Items functionality from frontend completely

export type ItemPublic = {
  id: string;
  title: string;
  description?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
};

export type ItemCreate = {
  title: string;
  description?: string;
};

export type ItemUpdate = {
  title?: string;
  description?: string;
};

export class ItemsService {
  static readItems(_params?: any): Promise<{ data: ItemPublic[]; count: number }> {
    return Promise.resolve({ data: [], count: 0 });
  }

  static createItem(_params: { requestBody: ItemCreate }): Promise<ItemPublic> {
    throw new Error('Items functionality has been removed');
  }

  static readItem(_params: { id: string }): Promise<ItemPublic> {
    throw new Error('Items functionality has been removed');
  }

  static updateItem(_id: string, _data: ItemUpdate): Promise<ItemPublic> {
    throw new Error('Items functionality has been removed');
  }

  static deleteItem(_id: string): Promise<void> {
    throw new Error('Items functionality has been removed');
  }
}
