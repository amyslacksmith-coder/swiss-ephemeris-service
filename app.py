// supabase/functions/calculate-astrology-western/index.ts

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const input = await req.json();

    const birthDate = input.birthDate;
    const birthTime = input.time;
    const latitude = input.latitude;
    const longitude = input.longitude;

    const houseSystem = input.houseSystem || "P";

    console.log("[calculate-astrology-western] houseSystem:", houseSystem);

    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;

    const authHeader = req.headers.get("Authorization") || "";

    const supabase = createClient(supabaseUrl, supabaseAnonKey, {
      global: {
        headers: {
          Authorization: authHeader,
        },
      },
    });

    const callEphemeris = async (
      birthDate: string,
      birthTime: string,
      latitude: number,
      longitude: number,
      houseSystem: string
    ) => {
      const { data, error } = await supabase.functions.invoke(
        "calculate-ephemeris-data",
        {
          body: {
            birthDate,
            time: birthTime,
            latitude,
            longitude,
            houseSystem,
          },
        }
      );

      if (error) throw error;
      return data;
    };

    const ephemeris = await callEphemeris(
      birthDate,
      birthTime,
      latitude,
      longitude,
      houseSystem
    );

    const usedHouseSystem =
      ephemeris?.houseSystem ?? ephemeris?.houses?.system ?? houseSystem;
    const usedHouseSystemName =
      ephemeris?.houseSystemName ?? ephemeris?.houses?.system_name ?? null;

    const result: any = {
      ...ephemeris,
      house_system: usedHouseSystem,
      house_system_name: usedHouseSystemName,
    };

    result.input_fingerprint = {
      birthDate,
      birthTime,
      latitude,
      longitude,
      house_system: houseSystem,
    };

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: String((error as any)?.message ?? error),
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
