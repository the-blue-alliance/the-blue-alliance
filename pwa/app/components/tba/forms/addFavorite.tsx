import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { useFetcher } from 'react-router';
import { z } from 'zod';

import { Button } from '~/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '~/components/ui/form';
import { Input } from '~/components/ui/input';

const formSchema = z.object({
  teamNumber: z.coerce
    .number()
    .min(1, { message: 'Team number must be at least 1' })
    .max(99999, {
      message: 'Team number must be less than 99999',
    }),
});

export default function AddFavoriteForm() {
  const fetcher = useFetcher();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      teamNumber: 0,
    },
  });

  function handleSubmit(data: z.infer<typeof formSchema>) {
    void fetcher.submit(data, {
      method: 'post',
      action: '/actions/addFavorite',
    });
  }

  return (
    <div>
      <h2 className="text-2xl font-medium">Add a Favorite</h2>
      <Form {...form}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void form.handleSubmit(handleSubmit)(e);
          }}
        >
          <FormField
            control={form.control}
            name="teamNumber"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Team Number</FormLabel>
                <FormControl>
                  <Input type="number" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit">Submit</Button>
        </form>
      </Form>
    </div>
  );
}
